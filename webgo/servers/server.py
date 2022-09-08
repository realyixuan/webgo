import logging
import socket
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

_logger = logging.getLogger(__name__)

ENCODING = 'iso-8859-1'


class Server:
    def __init__(self, address):
        self.address = address
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # import struct; sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

    def serve(self):
        self.sock.bind(self.address)
        try:
            self.sock.listen(1)
            _logger.info(f"server listening on {self.address}")
            while True:
                connection, address = self.sock.accept()
                self.process(connection, address)

        finally:
            self.sock.close()

    def process(self, connection, addr):
        environ = self.parse_http(connection, addr)
        self.handle(environ, connection)

    def parse_http(self, conn, addr):
        environ = {}

        http_io = HTTPSocketIO(conn)

        startline = http_io.readline()
        startline_items = startline.split()

        environ['REQUEST_METHOD'] = startline_items[0]
        environ['SERVER_PROTOCOL'] = startline_items[2]

        path, _, query_string = startline_items[1].partition('?')
        if query_string:
            environ['QUERY_STRING'] = query_string
        environ['PATH_INFO'] = path

        while request_header := http_io.readline():
            key, value = [v.strip() for v in request_header.split(':', maxsplit=1)]
            if key == 'Content-Type':
                environ['CONTENT-TYPE'] = value
            elif key == 'Content-Length':
                environ['CONTENT-LENGTH'] = int(value)
            elif key == 'Host':
                host, _, port = value.partition(':')
                environ['SERVER_NAME'] = host
                environ['SERVER_PORT'] = port or 80     # for http only
            environ[f'HTTP_{key.upper()}'] = value

        else:
            if environ.get('SERVER_NAME', '') == '':
                raise Exception

        # WSGI variables
        environ['wsgi.version'] = (1, 0)
        environ['wsgi.url_scheme'] = 'http'

        # put request body in
        environ['wsgi.input'] = ...

        environ['wsgi.errors'] = ...

        environ['wsgi.multithread'] = True
        environ['wsgi.multiprocess'] = False
        environ['wsgi.run_once'] = False

        return environ

    def handle(self, environ, connection):
        t = threading.Thread(target=self._handle, args=(environ, connection))
        t.start()

    def _handle(self, environ, connection):
        headers = []
        headers_sent = []

        def write(data):
            if not headers_sent:
                status, response_headers = headers_sent[:] = headers

                connection.sendall(f"HTTP/1.1 {status}\r\n".encode(ENCODING))
                for k, v in response_headers:
                    connection.sendall(f"{k}: {v}\r\n".encode(ENCODING))
                connection.sendall(b"\r\n")

            connection.sendall(data)

        def start_response(status, response_headers, exc_info=None):
            headers[:] = [status, response_headers]
            return write

        result = self.app(environ, start_response)
        _logger.info(f"{headers[0]}")

        if not headers_sent:
            headers[1].append(('Content-Length', len(result[0])))

        for data in result:
            write(data)

        connection.close()

    def set_app(self, app):
        self.app = app


class App:
    pass


def response(body, connection, address):
    response_headers = (
        "HTTP/1.1 200 OK\r\n",
        "Content-Type: text/html; charset=UTF-8\r\n",
        f"Content-Length: {len(body)}\r\n",
        "\r\n",
    )

    for header in response_headers:
        connection.sendall(header.encode('iso-8859-1'))
    connection.sendall(body.encode('utf8'))
    connection.sendall(b'the should not appear...')


def parser(connection, address):
    http_message = {}

    http_io = HTTPSocketIO(connection)
    start_line = http_io.readline()
    method, path, http_version = start_line.decode('iso-8859-1').strip().split()
    http_message['method'] = method

    if '?' in path:
        pure_path, params = path.split('?')
        http_message['path'] = pure_path
        http_message['params'] = {}
        for param_pair in params.split('&'):
            key, value = param_pair.split('=')
            http_message['params'][key] = value
    else:
        http_message['path'] = path
        http_message['params'] = {}

    http_message['http_version'] = http_version

    while (headerline := http_io.readline()) != b'\r\n':
        field, value = headerline.decode('iso-8859-1').split(':', 1)
        http_message[field] = value.strip()

    if 'Content-Length' not in http_message:
        return http_message

    http_message['body'] = http_io.read(http_message['Content-Length']).decode('iso-8859-1')

    return http_message


class HTTPSocketIO:
    def __init__(self, connection):
        self._connection = connection

    def readline(self):
        line = []
        while line[-2:] != [b'\r', b'\n']:
            byte_char = self._connection.recv(1)
            line.append(byte_char)
        return b''.join(line[:-2]).decode(ENCODING)

    def read(self, size):
        content = []
        total = 0
        while total >= size:
            data = self._connection.recv(size)
            content.append(data)
            total += len(data)
        return b''.join(content)


class HTTPMessage:
    def __init__(self):
        pass


def app(environ, start_response):
    print(environ)
    body = \
b"""\
Hello World
what the fuck
"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain')]
    start_response(status, headers)
    return [body]


if __name__ == '__main__':
    server = Server(('localhost', 8888))
    server.set_app(app)
    server.serve()
