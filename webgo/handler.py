def query(path):
    return lambda func: _Handler(func, path)


class _Handler:
    def __init__(self, func, path):
        self.origin_func = func
        self.path = path
    def response_attached(self):
        return self.origin_func()
