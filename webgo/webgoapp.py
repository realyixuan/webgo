import importlib

import webob


class Application:
    def __init__(self, module):
        self.handlers = route_mapping(module) 

    def build_response(self, request):
        path = request.path
        if path not in self.handlers:
            return webob.Response(text='Not Found')
        handler = self.handlers[path]
        return webob.Response(text=handler(request))

    def response(self, request):
        if request.method == 'GET':
            return self.build_response(request)
        else:
            return webob.Response(text='Not Yet Supported')

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        return self.response(request)(environ, start_response)


def route_mapping(module):
    handlers = {}
    aim_module = _import(module)
    for obj in aim_module.__dict__.values():
        if hasattr(obj, 'response_attached'):
            handlers[obj.path] = obj.response_attached
    return handlers


def _import(module_name):
    return importlib.import_module(module_name)


class NotFound(Exception):
    """ not yet implemented"""
