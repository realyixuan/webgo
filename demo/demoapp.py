from webgo.handler import get, post
from webgo.template import render


@get('/')
def index(request):
    return 'Hello World'

@post('/')
def post_test(request):
    return 'Have Fun'

@get('/wow')
def static_text(request):
    return render(request, 'demo/templates/index.html', context={
        'name': 'wow',
        'value': 'works',
    })

