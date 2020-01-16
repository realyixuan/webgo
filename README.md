# webgo

<img style="float: left;" src="https://img.shields.io/badge/python-3.6-blue">

A micro web framework

For instance, supposing there is a simplest demo.py:

~~~python
from webgo.handler import query

@query('/')
def index(request):
    return 'Hello World'
~~~

then, run it:

~~~bash
$ python __main__.py /YOUR_ABSOLUTE_PATH/demo.py
~~~

make a HTTP request:

~~~bash
$ curl http://localhost:8080
Hello World
~~~
