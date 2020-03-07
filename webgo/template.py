import mimetypes


def render(request, fname: str, context) -> str:
    with open(fname) as fp:
        text = fp.read()
    text_rendered = text
    if context:
        text_rendered = text_rendered.format(**context)
    return text_rendered


# def staticfile(path):
#     return lambda func: StaticFile(func, path)


class StaticFile:
    """ The class provides static file surface """
    def __init__(self, fpath):
        self.fpath = fpath
        self.mimetype, self.encoding = mimetypes.guess_type(self.fpath)

    def response_attached(self, request):
        return render(request, self.fpath, {})
