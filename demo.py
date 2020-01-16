from webgo.handler import query


@query('/')
def index(request):
    return 'Hello World'


@query('/wow')
def wow(request):
    return 'Wow, it works'


@query('/whatup')
def python(request):
    if request.method == 'GET':
        names = ['hello']
        for key, value in request.params.items():
            names.append(value)
        return ' '.join(names)

