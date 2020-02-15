from datetime import datetime

from webgo.handler import get, post
from webgo.template import render
from .model import Exam


@post('/')
def form(request):
    name = request.POST['name']
    exam = Exam(name=name, time=str(datetime.now()))
    exam.create()
    return 'LOG: ' + exam.name + exam.time


@get('/')
def static_text(request):
    return render(request, 'demo/templates/index.html', context={
        'name': 'wow',
        'value': 'works',
    })

