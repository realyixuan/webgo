import time
import logging
import socket

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

_logger = logging.getLogger(__name__)


class Server:
    def __init__(self, address):
        self.address = address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def serve(self):
        self.sock.bind(self.address)
        try:
            self.sock.listen(1)
            _logger.info(f"server listening on {self.address}")
            while True:
                time.sleep(0.5)
                connection, address = self.sock.accept()
                try:
                    http_message = parser(connection, address)
                    result = app(http_message)
                    if result:
                        response(result, connection, address)
                    _logger.info(f"successful processing request {http_message['method']} {http_message['path']}")
                finally:
                    connection.close()
        finally:
            self.sock.close()


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
        return b''.join(line)

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


def app(request):
    if request['path'] == '/':
        if 'name' in request['params']:
            return f"<h1>hello {request['params']['name']}</h1>"
        else:
            return "hello world"
    else:
        return None


if __name__ == '__main__':
    Server(('localhost', 9002)).serve()
