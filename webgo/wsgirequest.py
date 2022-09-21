import json


class Request:
    def __init__(self, environ):
        self._environ = environ
        self._buffer = b''

    @property
    def POST(self):
        return self.body

    @property
    def buffer(self):
        content_length = int(self._environ['CONTENT_LENGTH'])
        if not self._buffer:
            stream = self._environ['wsgi.input']
            while content_length > 0:
                c = stream.read(1)
                self._buffer += c
                content_length -= 1
        return self._buffer

    @property
    def body(self):
        res = {}
        body_string = self.buffer.decode('iso-8859-1')

        if self._environ['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            for pair in body_string.split('&'):
                k, v = pair.split('=')
                res[k] = v.replace('+', ' ')
        elif self._environ['CONTENT_TYPE'] == 'application/json':
            res = json.loads(body_string)

        return res

    @property
    def path(self):
        return self._environ['PATH_INFO']

    @property
    def method(self):
        return self._environ['REQUEST_METHOD']


class Response:
    def __init__(self, body=None, content_type='text/html'):
        self.body = body
        self.content_type = content_type

    @property
    def status(self):
        return '200 OK'

    @property
    def content_length(self):
        return len(self.body)

    @property
    def headers(self):
        return [
            ('Content-type', self.content_type),
        ]

    def __iter__(self):
        yield self.body.encode('iso-8859-1')
