from webgo.handler import query
from webgo.template import render


@query('/')
def index(request):
    return 'Hello World'


@query('/whatup')
def python(request):
    if request.method == 'GET':
        name, value = 'Python', 'Nice'
        if request.params:
            name, value = 'name', request.params.getone('name')
    return render(request, 'index.html', context={
        'name': name,
        'value': value,
    })

