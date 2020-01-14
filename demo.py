from webgo.handler import query


@query('/')
def index():
    return 'Hello World'


@query('/yes/wow')
def wow():
    return 'Wow, it works'


@query('/python')
def python():
    return 'Hello, Python'
