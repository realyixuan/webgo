import os
import sys
import types
import logging
import argparse
from multiprocessing.pool import ThreadPool
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
from importlib.abc import Loader, MetaPathFinder
from importlib.util import spec_from_file_location

from webgo import config
from webgo import webgoapp
from webgo.template import get_abs_path

logger = logging.getLogger(__name__)


def serving(Application=webgoapp.Application):
    PROJECT_PATH = parse_command_argument()
    config.project = config.ProjectParse(PROJECT_PATH)

    sys.meta_path.append(WebgoMetaPathFinder())

    app = Application(config.project.pkg_name)

    # Reload file if file modified
    app = Reload(app, config.project.path)

    logger.info(f'Serving {config.project.pkg_name} ... ')

    run_server(app)


def run_server(app):
    make_server('', 8080, app).serve_forever()


class TheadPoolWSGIServer(WSGIServer):
    def __init__(self, workers, *args, **kwargs):
        WSGIServer.__init__(self, *args, **kwargs)
        self.workers = workers
        self.pool = ThreadPool(self.workers)

    def process_request(self, request, client_address):
        self.pool.apply_async(
            WSGIServer.process_request,
            args=(self, request, client_address)
        )


def make_server(
        host,
        port,
        app,
        handler_class=WSGIRequestHandler,
        workers=8
):
    httpd = TheadPoolWSGIServer(
        workers=workers,
        server_address=(host, port),
        RequestHandlerClass=handler_class
    )
    httpd.set_app(app)
    return httpd


class WebgoMetaPathFinder(MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        modname = config.project.pkg_name
        location = os.path.join(config.project.path, '__init__.py')

        if fullname == modname:
            return spec_from_file_location(
                name=modname,
                location=location,
                loader=WebgoLoader(),
                submodule_search_locations=[config.project.path]
            )
        else:
            return None


class WebgoLoader(Loader):
    def create_module(self, spec):
        return None

    def exec_module(self, module):
        with open(module.__file__) as f:
            data = f.read()
        exec(data, module.__dict__)

    def module_repr(self, module):
        return NotImplementedError


def parse_command_argument():
    parser = argparse.ArgumentParser()
    parser.add_argument('project', help='your project')
    parser.add_argument('--migrate', help='migrate your model')
    args = parser.parse_args()

    # if args.migrate:
        # The operation is somewhat funny!
        # _load_module(get_abs_path(args.project))
        # orm.Model.create_table(args.migrate)
        # sys.exit()

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
            logger.info(f'Reloading {self.project} ... ')
            self.app.__init__(config.project.pkg_name)
            self.mtime = mtime_now
        return self.app(environ, start_response)
