import os
import importlib
import inspect

import webob

from webgo.template import StaticFile


class Application:
    """ Create a WSGI application """
    def __init__(self, package: str):
        self.handlers = route_mapping(package)

    def build_response(self, request):
        path = request.path
        handlers = self.handlers[request.method]
        if path not in handlers:
            return webob.Response(text='Not Found')
        handler = handlers[path]
        if hasattr(handler.__self__, 'mimetype'):
            mime_type = handler.__self__.mimetype
            return webob.Response(text=handler(request),
                                  content_type=mime_type)
        return webob.Response(text=handler(request))

    def response(self, request):
        return self.build_response(request)

    def static_file(self):
        pass

    def __call__(self, environ, start_response):
        request = webob.Request(environ)
        return self.response(request)(environ, start_response)


def route_mapping(upackage: str) -> dict:
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
                handlers[obj.method][obj.path] = obj.response_attached

    # root_path = os.path.dirname(package.__file__)
    root_path = package.__path__[0]
    handlers['GET'].update(staticfile_route_mapping(root_path))
    return handlers


def staticfile_route_mapping(root_path):
    """ Mapping static file
    The static directory hierarchy:

    ├── static
    │   ├── css
    │   │   └── demo.css
    │   └── js
    │       └── demo.js
    └── templates
        └── index.html
    """
    def _get_all_filepath(path, res: list):
        # Put all files' path under `path` into res
        for filename in os.listdir(path):
            subpath = os.path.join(path, filename)
            if os.path.isdir(subpath):
                _get_all_filepath(subpath, res)
            else:
                res.append(subpath)

    static_dir = 'static'
    static_path = os.path.join(root_path, static_dir)
    static_files_path = res = []
    _get_all_filepath(static_path, res)
    handlers = {}
    for path in static_files_path:
        handlers[path[len(root_path):]] = StaticFile(path).response_attached
    return handlers


def _import(module_name):
    return importlib.import_module(module_name)


class NotFound(Exception):
    """ not yet implemented"""
