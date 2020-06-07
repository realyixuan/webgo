import os
import mimetypes

from jinja2 import Environment, FileSystemLoader

from webgo import config


env = None


def render(request, fname: str, context) -> str:
    global env

    if not env:
        template_path = os.path.join(config.project.path, 'templates')
        file_loader = FileSystemLoader(template_path)
        env = Environment(loader=file_loader)

    template = env.get_template(fname)
    output = template.render(context)
    return output


def _get_static_content(fpath):
    with open(fpath) as fp:
        text = fp.read()
    return text

# def staticfile(path):
#     return lambda func: StaticFile(func, path)


class StaticFile:
    """ The class provides static file surface """
    def __init__(self, fpath):
        self.fpath = fpath
        self.mimetype, self.encoding = mimetypes.guess_type(self.fpath)

    def response_attached(self, request):
        return _get_static_content(self.fpath)


def get_abs_path(path):
    return os.path.join(os.getcwd(), path)

