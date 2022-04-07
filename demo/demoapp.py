import time
from datetime import datetime

from webgo.handler import get, post
from webgo.template import render

from .model import Exam
from webgo.orm import User


@post('/')
def form(request):
    name = request.POST['name']

    user = User(name='Guido', age=65)
    user.save()

    # Create a record
    exam = Exam(name=name, time=str(datetime.now()))

    exam.user = 1

    # Save it to database
    exam.save()

    b = exam.user

    # Select all record in 'Exam' table
    all_rec = Exam.objects.query()
    return '<br>'.join('LOG: ' + item.name + item.time for item in all_rec)


@get('/')
def static_text(request):
    return render(request, 'index.html', context={
        'value': 'Login Log',
    })


@get('/hello')
def hello(request):
    time.sleep(1)
    return 'Hello World'
