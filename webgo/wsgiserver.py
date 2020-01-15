import os
import sys
import types
import argparse
from wsgiref.simple_server import make_server

from . import webgoapp


def serving(Application=webgoapp.Application):
    # file_ must be a absolute path
    file_ = parse_command_argument()
    module_name = _load_module(file_)
    app = Application(module_name)
    
    app = Reload(app, file_)

    print(f'Serving { module_name } ... ')
    run_server(app)


def run_server(app):
    make_server('', 8080, app).serve_forever()


def _load_module(file_):
    mname = 'webgo__main__'
    module = types.ModuleType(mname)
    module.__file__ = file_
    with open(module.__file__) as fp:
        exec(fp.read(), module.__dict__)
    sys.modules[module.__name__] = module
    return module.__name__


def parse_command_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('view_file', help='your absolute view file path')
    args = parser.parse_args()

    return args.view_file


class Reload:
    """ Module-reload Middleware """
    def __init__(self, app, file_):
        self.app = app
        self.file_ = file_
        self.mtime = os.stat(file_).st_mtime

    def __call__(self, environ, start_response):
        mtime_now = os.stat(self.file_).st_mtime
        if mtime_now != self.mtime:
            print(f'Reloading { self.file_ } ... ')
            module_name = _load_module(self.file_)
            self.app.__init__(module_name)
            self.mtime = mtime_now
        return self.app(environ, start_response)


