from wsgiref.simple_server import make_server

from application import Application


def run_server(app, port):
    make_server('', port, app).serve_forever()


def server(args=None, Application=Application):
    port = 8080
    print(f'Serving on port { port } ... ')
    run_server(Application, port)
