import sys
import types
import argparse
from wsgiref.simple_server import make_server

from . import app


def run_server(app):
    make_server('', 8080, app).serve_forever()


def serving(Application=app.Application):
    parser = argparse.ArgumentParser()
    parser.add_argument('view_file', help='your absolute view file path')
    args = parser.parse_args()

    path = args.view_file

    mname = 'webgo__main__'
    module = types.ModuleType(mname)
    module.__file__ = path
    with open(module.__file__) as fp:
        exec(fp.read(), module.__dict__)
    sys.modules[module.__name__] = module
    pyfile = module.__name__
    Application = Application(pyfile)

    print(f'Serving { pyfile } ... ')
    run_server(Application)
