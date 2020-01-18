def get(path):
    return _query(path, method='GET')


def post(path):
    return _query(path, method='POST')


def _query(path, method):
    return lambda func: _Handler(func, path, method=method)


class _Handler:
    def __init__(self, func, path, method):
        self.origin_func = func
        self.path = path
        self.method = method

    def response_attached(self, request):
        return self.origin_func(request)
        
