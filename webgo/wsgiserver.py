import os
import sys
import types
import argparse
from wsgiref.simple_server import make_server

from . import webgoapp
from .fileoperation import get_abs_path 


def serving(Application=webgoapp.Application):
    project = parse_command_argument()
    package = _load_module(project)
    app = Application(package)
    
    # Reload file if file modified
    app = Reload(app, project)

    print(f'Serving { package } ... ')
    run_server(app)


def run_server(app):
    make_server('', 8080, app).serve_forever()


def _load_module(file_: str) -> str:
    mname = os.path.basename(file_)
    module = types.ModuleType(mname)
    module.__file__ = os.path.join(file_, '__init__.py')
    with open(module.__file__) as fp:
        exec(fp.read(), module.__dict__)
    sys.modules[module.__name__] = module
    return module.__name__


def parse_command_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', help='your project')
    args = parser.parse_args()

    return get_abs_path(args.project)


class Reload:
    """ Module-reload Middleware """
    def __init__(self, app, project):
        self.app = app
        self.project = project
        self.mtime = os.path.getctime(project)

    def __call__(self, environ, start_response):
        mtime_now = os.path.getctime(self.project)
        if mtime_now != self.mtime:
            print(f'Reloading { self.project } ... ')
            package = _load_module(self.project)
            self.app.__init__(package)
            self.mtime = mtime_now
        return self.app(environ, start_response)


