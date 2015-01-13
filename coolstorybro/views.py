import json
import base64
import pprint
from urlparse import (
 urlparse,
 parse_qs
)

from pyramid.view import view_config
import os
from pyramid.response import Response
import re
import jwt

from .jira.api import Client as JiraClient


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'coolstorybro'}

@view_config(name='atlassian-connect.json')
def descriptor_view(request):
    print request
    print request.scheme
    json_data = open(os.path.join(os.path.dirname(__file__), 'descriptor.json'))
    data = json.load(json_data)
    data['baseUrl'] = request.application_url

    secure_domains = ['.*\.localtunnel\.me', '.*\.herokuapp\.com']

    for sd in secure_domains:
        match = re.match(sd, data['baseUrl'])
        if match is not None:
            data['baseUrl'] = re.sub('^http:', 'https:', data['baseUrl'])
            break

    return Response(json.dumps(data), 200, content_type='application/json')


# Add-on life-cycle callbacks

@view_config(name="installed")
def lifecycle_installed_view(request):
    data = request.json_body
    print data
    manager = request.jira_token_mgr
    if (data):
        manager.set(data['clientKey'], data['sharedSecret'])
        return Response('OK!')
    else:
        return Response('Invalid data.', 400)

@view_config(name="uninstalled")
def lifecycle_uninstalled_view(request):
    data = request.json_body
    manager = request.jira_token_mgr
    if (data):
        manager.delete(data['clientKey'])
        return Response('OK!')
    else:
        return Response('Invalid data.', 400)

@view_config(name="configure-instance", renderer="templates/configure.pt")
@view_config(name="instance-configuration", renderer="templates/configure.pt")
def configure_instance_view(request):

    tokens = request.jira_token_mgr
    jwt_info = jwt.decode(request.params['jwt'], verify=False)
    secret = tokens.get(jwt_info['iss'])

    if request.referer:
        jira_url = re.sub('\/plugins\/servlet\/ac\/.*', '', request.referer)
    else:
        jira_url = 'http://localhost:2990/jira'

    api_url = jira_url
    if api_url == 'http://localhost:2990/jira':
        api_url = 'http://jira-local:2990/jira'

    client = JiraClient(host=api_url, issuer='com.activelamp.coolstorybro', secret=secret)

    parts = urlparse(request.referer)
    qs_params = parse_qs(parts.query)

    project_key = qs_params['project.key'][0]

    res = client.get(uri='/rest/api/latest/project/' + project_key)
    project = res.json()
    statuses_res = client.get(uri=project['self'] + '/statuses')
    statuses = statuses_res.json()
    print pprint.pformat(statuses)

    subtask_types = [itype for itype in statuses if itype['subtask'] == True]
    parent_types = [itype for itype in statuses if itype['subtask'] == False]

    config_mgr = request.jira_project_config_mgr
    if config_mgr.has_config(project_id=str(project['id']), client_key=jwt_info['iss']):
        project_config = config_mgr.get_config(project_id=str(project['id']), client_key=jwt_info['iss'])
    else:
        project_config = None

    host_script_base_url = re.sub('^https?:', '', jira_url)
    return {
        'project': project,
        'subtask_types': subtask_types,
        'parent_types': parent_types,
        'host_script_base_url': host_script_base_url,
        'client_id': jwt_info['iss'],
        'config_endpoint': request.resource_path(request.context, 'save-configuration'),
        'enable_endpoint': request.resource_path(request.context, 'enable-project'),
        'project_config': "{}" if project_config is None else project_config.configuration,
        'enabled': False if project_config is None else project_config.enabled
    }

@view_config(name='save-configuration')
def save_configuration_view(request):
    data = request.json_body
    request.jira_token_mgr.get(data['client_id'])  # Raises exception if JIRA instance is recognized.

    config_mgr = request.jira_project_config_mgr
    config_mgr.save_data(client_key=data['client_id'], project_id=data['project_id'], configuration=data['issue_type'])

    return Response('OK!')

@view_config(name='enable-project')
def enable_automation_view(request):
    request.jira_token_mgr.get(request.params['client_id'])  # Raises exception if JIRA instance is recognized.
    config_mgr = request.jira_project_config_mgr
    if request.params['action'] == 'enable':
        config_mgr.enable(client_key=request.params['client_id'], project_id=request.params['project_id'])
    else:
        config_mgr.disable(client_key=request.params['client_id'], project_id=request.params['project_id'])
    return Response('OK!')


# Webhook callbacks
@view_config(route_name="webhook")
def webhook_view(request):
    # Only allow JWT authenticated requests.
    auth = request.authorization

    if auth[0] != 'JWT':
        return Response('Not OK.', status=400)
    token = auth[1]
    claims = json.loads(base64.b64decode(token.split('.')[1] + '=='))

    # Check if JIRA instance is registered with us.
    manager = request.jira_token_mgr
    try:
        secret = manager.get(claims['iss'])
    except:
        raise ValueError('Unknown JIRA instance.')

    data = request.json_body
    if data['webhookEvent'] == 'jira:issue_created':
        __on_issue_created(data, secret, request)
    elif data['webhookEvent'] in ['jira:issue_updated', 'remote_issue_link_aggregate_cleared_event']:
        __on_issue_updated(data, secret, request)
    elif data['webhookEvent'] == 'jira:issue_deleted':
        __on_issue_deleted(data, secret, request)

    return Response('OK!')

# Internals

STORY_POINT_FIELD_ID = 'customfield_10004'

def __on_issue_updated(data, secret, request):
    """
    Called when jira:issue_updated or remote_issue_link_aggregate_cleared_event notification is received.

    :param data:
    :param secret:
    :param request:
    :return:
    """
    host = __extract_jira_host(data['issue']['self'])
    client = JiraClient(host=host, secret=secret, issuer='com.activelamp.coolstorybro')

    #  Return if issue doesn't have a parent.
    if not data['issue']['fields'].has_key('parent'):
        return None

    diff = None
    #  Check if the summary is one of the fields updated.
    for change in data['changelog']['items']:
        if change['field'] == 'summary':
            #  Calculate the change of estimate
            estimate_from = __extract_estimate_from_string(change['fromString'])
            estimate_to = __extract_estimate_from_string(change['toString'])
            if estimate_from is None:
                estimate_from = 0
            diff = estimate_to - estimate_from
            break

    if diff is not None:
        __update_issue_story_point(client, data['issue']['fields']['parent'], diff)

def __on_issue_created(data, secret, request):
    """
    Called when jira:issue_created notification is received.

    :param data:
    :param secret:
    :param request:
    :return:
    """
    host = __extract_jira_host(data['issue']['self'])
    client = JiraClient(host=host, secret=secret, issuer='com.activelamp.coolstorybro')

    estimate = __extract_estimate(data['issue'])
    if estimate is None:
        return None

    if data['issue']['fields'].has_key('parent'):
        __update_issue_story_point(client, data['issue']['fields']['parent'], estimate)

def __on_issue_deleted(data, secret, request):
    """
    Called when jira:issue_deleted notification is received.

    :param data:
    :param secret:
    :param request:
    :return:
    """
    host = __extract_jira_host(data['issue']['self'])
    client = JiraClient(host=host, secret=secret, issuer='com.activelamp.coolstorybro')

    estimate = __extract_estimate(data['issue'])
    if estimate is None:
        return None

    if data['issue']['fields'].has_key('parent'):
        __update_issue_story_point(client, data['issue']['fields']['parent'], 0 - estimate)

def __extract_jira_host(issue_url):
    """
    Determine the JIRA base URL from the given issue REST URL
    :param issue_url:
    :return:
    """
    matches = re.findall('(.*)\/rest.*', issue_url)
    return matches[0]

def __extract_estimate(issue_data):
    """
    Extract estimate from the issue summary.

    :param issue_data:
    :return:
    """
    return __extract_estimate_from_string(issue_data['fields']['summary'])

def __extract_estimate_from_string(s):
    """
    Extract estimate from string, possibly an issue summary.

    Example string:
        (10) As an Atlassian app, I shoud be able to listen to event notifications when an issue has created, changed, or deleted.

        In this example, the estimate is 10

    :param s:
    :return:
    """
    match = re.search(r'^\((\d+)\)', s)
    if match is not None:
        return float(match.group(1))

def __update_issue_story_point(client, parent_issue, story_point_diff):
    """
    Updates a parent issue's story point with the story point diff.
    If the story point diff is positive, the value is added. Otherwise, it is removed.

    :param client: JiraClient
    :param parent_issue:
    :param story_point_diff:
    :return:
    """
    res = client.get(parent_issue['self'])
    parent_data = res.json()
    if parent_data['fields'].has_key(STORY_POINT_FIELD_ID):
        story_point = parent_data['fields'][STORY_POINT_FIELD_ID]
        if story_point is None:
            story_point = 0
        new_story_point = float(story_point) + float(story_point_diff)
        put_res = client.put(parent_data['self'], data={
            'fields': {
                STORY_POINT_FIELD_ID: new_story_point
            }
        })
        print put_res.status_code
