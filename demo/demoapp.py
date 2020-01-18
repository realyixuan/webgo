from webgo.handler import get, post
from webgo.template import render, staticfile


@get('/')
def index(request):
    return 'Hello World'

@post('/')
def post_test(request):
    return 'Have Fun'



# @query('/whatup')
# def python(request):
#     if request.method == 'GET':
#         name, value = 'Python', 'Nice'
#         if request.params:
#             name, value = 'name', request.params.getone('name')
#     return render(request, 'index.html', context={
#         'name': name,
#         'value': value,
#     })
# 
# @staticfile('/demo.css')
# def static(request):
#     return render(request, 'demo.css', {})
