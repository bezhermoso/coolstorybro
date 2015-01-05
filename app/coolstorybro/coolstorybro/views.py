from pyramid.view import view_config
import os
from pyramid.response import FileResponse
from pyramid.response import Response
from tokens import manager
import json

@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'coolstorybro'}

@view_config(name='atlassian-connect.json')
def descriptor_view(request):
    json_data = open(os.path.join(os.path.dirname(__file__), 'descriptor.json'))
    data = json.load(json_data)
    data['baseUrl'] = request.application_url
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
    return Response('OK!')
    pass

