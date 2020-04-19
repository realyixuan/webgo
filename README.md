# webgo

Webgo is a micro web framework.

It addresses a couple of problems:

- Mapping URL to objects

- Loading static files

- Performing DB operations through ORM 

## Requirements

Python 3.6+

## Installation

~~~
$ pip3 install webgo
~~~

## Quickstart

*There is a simple implementation in `demo` directory, You can imitate it to build your own.*

**run**

~~~
$ webgo demo
~~~

*and access: http://localhost:8080*

### More

**Project Structure**

You must construct project structure like this:

And import all `.py` files in `__init__.py`

~~~
.
├── __init__.py
├── app.py
├── model.py
├── static
│   ├── css
│   │   └── demo.css
│   └── js
│       └── demo.js
└── templates
    └── index.html
~~~

**Object Mapping**

You can map any URL to any function.

~~~
from webgo.handler import get

@get('/')
def hello(request):
    return 'hello world'
~~~

**ORM**

You can save and query data through sqlite by orm.

~~~
>>> from webgo.orm import IntegerField, TextField, Model
>>> class Demo(Model): 
>>>     age = IntegerField('age') 
>>>     name = TextField('name') 

>>> Model.create_table()                                                
Table Demo created

>>> one = Demo(age=12, name='Bob')                                          

>>> one.age = 15                                                           

>>>  one.save()                                                             

>>>  one.pk                                                                 
>>>  1

>>>  one.age                                                               
>>>  15

>>> Demo(age=10, name='Tom').save()

>>> recset = Demo.objects.query()

>>> print(recset)
<Demo RecorcdSet (1,2)>
~~~

