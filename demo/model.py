from webgo.orm import Model
from webgo.orm import TextField, Many2one


class Exam(Model):
    name = TextField()
    time = TextField()
    user = Many2one(related_model='User')
