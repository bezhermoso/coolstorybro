from pyramid.view import view_config
import os
from pyramid.response import Response
from pyramid.request import Request
from tokens import manager
import json
import re
import pprint
import jwt
import base64

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'coolstorybro'}

@view_config(name='atlassian-connect.json')
def descriptor_view(request):
    json_data = open(os.path.join(os.path.dirname(__file__), 'descriptor.json'))
    data = json.load(json_data)
    data['baseUrl'] = request.application_url
    match = re.match('.*\.localtunnel\.me', data['baseUrl'])
    if match is not None:
        data['baseUrl'] = re.sub('^http:', 'https:', data['baseUrl'])
    return Response(json.dumps(data), 200, content_type='application/json')


# Add-on life-cycle callbacks

@view_config(name="installed")
def lifecycle_installed_view(request):
    data = request.json_body
    if (data):
        manager.set(data['clientKey'], data['sharedSecret'])
        return Response('OK!')
    else:
        return Response('Invalid data.', 400)

@view_config(name="uninstalled")
def lifecycle_uninstalled_view(request):
    print request
    data = request.json_body
    if (data):
        manager.delete(data['clientKey'])
        return Response('OK!')
    else:
        return Response('Invalid data.', 400)

# Webhook callbacks
@view_config(route_name="webhook")
def webhook_view(request):
    print request
    auth = request.authorization
    if auth[0] != 'JWT':
        return Response('Not OK.', status=400)
    token = auth[1]
    claims = json.loads(base64.b64decode(token.split('.')[1] + '=='))
    try:
        secret = manager.get(claims['iss'])
        print secret
    except:
        raise ValueError('Unknown JIRA instance.')
    return Response('OK!')
    pass


def _qhash(request):
    # Implement hashing from: https://developer.atlassian.com/static/connect/docs/concepts/understanding-jwt.html
    return ''