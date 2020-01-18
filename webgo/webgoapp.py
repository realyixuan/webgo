import importlib
import inspect

import webob


class Application:
    def __init__(self, package: str):
        self.handlers = route_mapping(package) 

    def build_response(self, request):
        path = request.path
        handlers = self.handlers[request.method]
        if path not in handlers:
            return webob.Response(text='Not Found')
        handler = handlers[path]
        if hasattr(handler, 'static_mime'):
            mime_type = handler.static_mime()
            return webob.Response(text=handler.response_attached(request),
                                  content_type=mime_type)
        return webob.Response(text=handler.response_attached(request))

    def response(self, request):
        return self.build_response(request)

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        return self.response(request)(environ, start_response)


def route_mapping(upackage: str):
    handlers = {
        'GET': {},
        'POST': {},
        }
    package = _import(upackage)
    for module in package.__dict__.values():
        if not hasattr(module, '__dict__'):
            continue
        for obj in module.__dict__.values():
            if hasattr(obj, 'response_attached'):
                handlers[obj.method][obj.path] = obj
    return handlers


def _import(module_name):
    return importlib.import_module(module_name)


class NotFound(Exception):
    """ not yet implemented"""
