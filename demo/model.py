from webgo.orm import Model
from webgo.orm import TextField


class Exam(Model):
    name = TextField('name')
    time = TextField('time')
