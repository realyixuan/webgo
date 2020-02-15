import os
import sys
import types
import argparse
from wsgiref.simple_server import make_server

from . import webgoapp
from .fileoperation import get_abs_path
from . import config
from . import orm


def serving(Application=webgoapp.Application):
    config.PROJECT_PATH = parse_command_argument()
    package_name = _load_module(config.PROJECT_PATH)
    app = Application(package_name)
    
    # Reload file if file modified
    app = Reload(app, config.PROJECT_PATH)

    print(f'Serving { package_name } ... ')
    run_server(app)


def run_server(app):
    make_server('', 8080, app).serve_forever()


def _load_module(project_path: str) -> str:
    # Maybe the way importing module isn't normal
    # May there be a good way?
    project_name = os.path.basename(project_path)
    mname = project_name + '__main__'
    module = types.ModuleType(mname)
    module.__path__ = project_path
    module.__package__ = project_name
    module.__file__ = os.path.join(project_path, '__init__.py')
    with open(module.__file__) as fp:
        exec(fp.read(), module.__dict__)
    sys.modules[module.__name__] = module
    return module.__name__


def parse_command_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', help='your project')
    parser.add_argument('--migrate', help='migrate your model')
    args = parser.parse_args()

    if args.migrate:
        # The operation is somewhat funny!
        _load_module(get_abs_path(args.project))
        orm.Model.create_table(args.migrate)
        sys.exit()

    return get_abs_path(args.project)


class Reload:
    """ Module-reload Middleware """
    def __init__(self, app, project_path):
        self.app = app
        self.project = project_path
        self.mtime = os.path.getctime(project_path)

    def __call__(self, environ, start_response):
        mtime_now = os.path.getctime(self.project)
        if mtime_now != self.mtime:
            print(f'Reloading { self.project } ... ')
            package = _load_module(self.project)
            self.app.__init__(package)
            self.mtime = mtime_now
        return self.app(environ, start_response)


