def render(request, fname: str, context) -> str:
    with open(fname) as fp:
        text = fp.read()
    text_rendered = text
    if context:
        text_rendered = text_rendered.format(**context)
    return text_rendered


def staticfile(path):
    return lambda func: StaticFile(func, path)


class StaticFile:
    def __init__(self, func, path):
        self.origin_func = func
        self.path = path

    def response_attached(self, request):
        return self.origin_func(request)
        
    def static_mime(self):
        return 'text/css'
