from pyramid.view import view_config
import os
from pyramid.response import FileResponse
from pyramid.response import Response


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def my_view(request):
    return {'project': 'coolstorybro'}

@view_config(name='atlassian-connect.json')
def descriptor_view(request):
    return FileResponse(os.path.join(os.path.dirname(__file__), 'descriptor.json'), request=request)

# Add-on life-cycle callbacks

@view_config(name="installed")
def lifecycle_installed_view(request):
    print request
    return Response('Foo!')

@view_config(name="uninstalled")
def lifecycle_uninstalled_view(request):
    pass

