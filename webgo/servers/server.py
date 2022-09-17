import logging
import socket
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

_logger = logging.getLogger(__name__)

ENCODING = 'iso-8859-1'


class InputStream:
    def __init__(self, conn, remains=0):
        self._conn = conn
        self._remains = remains

    def read(self, size=-1):
        if self._remains <= 0:
            return b''

        if size < 0:
            sz = self._remains
        else:
            sz = min(size, self._remains)
        data = self._conn.recv(sz)
        self._remains -= len(data)
        return data

    def readline(self, size=-1):
        if size < 0:
            sz = self._remains
        else:
            sz = min(size, self._remains)

        line = []
        while (
                sz > len(line)
                and (not line or line[-1] != '\n')
        ):
            c = self._conn.recv(1)
            if not c:
                break
            line.append(c)
        self._remains -= len(line)
        return b''.join(line)

    def readlines(self):
        return [line for line in self.readline()]

    def __iter__(self):
        while self._remains > 0:
            yield self.read(1)


class ErrorStream:
    def __init__(self, conn):
        self._conn = conn

    def flush(self):
        """ no-op """

    def write(self, b):
        return self._conn.send(b)

    def writelines(self, seq):
        for line in seq:
            self._conn.sendall(line)


class Server:
    def __init__(self, address):
        self.address = address
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # import struct; sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))

    def serve_forever(self):
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
        """
        Since PEP3333 states: "..., the environ dictionary MAY also contain arbitrary operating-system “environment variables”, ..."
        so skip over it.
        """
        environ = {}

        http_io = HTTPSocketIO(conn)

        startline = http_io.readline().decode(ENCODING)
        startline_items = startline.split()

        environ['REQUEST_METHOD'] = startline_items[0]
        environ['SERVER_PROTOCOL'] = startline_items[2]

        path, _, query_string = startline_items[1].partition('?')
        if query_string:
            environ['QUERY_STRING'] = query_string
        environ['PATH_INFO'] = path

        while (request_header := http_io.readline().decode(ENCODING)) not in ('\r\n', '\n', ''):
            key, value = [v.strip() for v in request_header.split(':', maxsplit=1)]
            if key == 'Content-Type':
                environ['CONTENT_TYPE'] = value
            elif key == 'Content-Length':
                environ['CONTENT_LENGTH'] = int(value)
            elif key == 'Host':
                host, _, port = value.partition(':')
                environ['SERVER_NAME'] = host
                environ['SERVER_PORT'] = port or 80     # for http only
            environ[f"HTTP_{key.upper().replace('-', '_')}"] = value

        else:
            if environ.get('SERVER_NAME', '') == '':
                raise Exception

        # WSGI variables
        environ['wsgi.version'] = (1, 0)
        environ['wsgi.url_scheme'] = 'http'

        environ['wsgi.input'] = InputStream(conn, environ.get('CONTENT_LENGTH', 0))

        environ['wsgi.errors'] = ErrorStream(conn)

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
            if exc_info:
                # If headers has been sent already, raise original exception,
                # because, at this time, can't change headers anymore
                if headers_sent:
                    raise exc_info[1].with_traceback(exc_info[2])
            elif headers:
                raise AssertionError('Headers already set')
            headers[:] = [status, [(k, v) for k, v in response_headers if k != 'Content-Length']]
            return write

        result = self.app(environ, start_response)
        _logger.info(f"{headers[0]}")

        if not headers_sent:
            headers[1].append(('Content-Length', len(result[0])))
            headers[1].append(('Server', 'WebgoServer'))
            headers[1].append(('Date', datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')))

        try:
            for data in result:
                if data:
                    write(data)
        finally:
            if hasattr(result, 'close'):
                result.close()

        connection.close()

    def set_app(self, app):
        self.app = app


class HTTPSocketIO:
    def __init__(self, connection):
        self._connection = connection

    def readline(self):
        line = []
        # XXX: recognize a single LF as a line terminator and ignore the leading CR.
        # refer to: https://www.rfc-editor.org/rfc/rfc2616#section-19.3
        while not line\
                or (line[-1] != b'\n' and line[-1] != b''):
            byte_char = self._connection.recv(1)
            line.append(byte_char)
        return b''.join(line)

    def read(self, size):
        content = []
        total = 0
        while total >= size:
            data = self._connection.recv(size)
            content.append(data)
            total += len(data)
        return b''.join(content)
