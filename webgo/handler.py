import webob
from typing import Callable, NewType

Request = NewType('Request', webob.Request)


def get(path):
    return _query(path, method='GET')


def post(path):
    return _query(path, method='POST')


def _query(path, method):
    return lambda func: _Handler(func, path, method=method)


class _Handler:
    """ Handlers wrap functions to provide resource interface
    They handle requests by calling the underlying functions
    """
    def __init__(self, func: Callable[[Request], str], path, method):
        self.origin_func = func
        self.path = path
        self.method = method

    def response_attached(self, request) -> str:
        return self.origin_func(request)

