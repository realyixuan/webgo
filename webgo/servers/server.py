import logging
import socket

_logger = logging.getLogger(__name__)


class Server:
    def __init__(self, address):
        self.address = address

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(self.address)
        try:
            sock.listen(1)
            connection, address = sock.accept()
            try:
                http_message = parser(connection, address)
                result = app(http_message)
                response(result, connection, address)
            finally:
                connection.close()
        finally:
            sock.close()


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


def parser(connection, address):
    http_message = {}

    http_io = HTTPSocketIO(connection)
    start_line = http_io.readline()
    method, path, http_version = start_line.decode('iso-8859-1').strip().split()
    http_message['method'] = method
    http_message['path'] = path
    http_message['http_version'] = http_version

    while (headerline := http_io.readline()) != b'\r\n':
        print(headerline)
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
    return f"hello {request['User-Agent']}"


if __name__ == '__main__':
    Server(('localhost', 9001)).serve()
