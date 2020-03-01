import os
import pytest
import sqlite3

from webgo import config
config.DB_FILE="/home/yixuan/github/webgo/tests/files/sqlite.db"
from webgo.exceptions import FieldError
from webgo.orm import Model, IntegerField, TextField


@pytest.fixture(scope='module')
def test_client():
    if os.path.exists(config.DB_FILE):
        os.remove(config.DB_FILE)
    class TestModel(Model):
        name = TextField('name')
        age = IntegerField('age')
    Model.create_table('TestModel')
    return TestModel


def test_field_id():
    with pytest.raises(FieldError):
        class User(Model):
            pk = IntegerField('pk')


def test_cduq(test_client):
    test_client.objects.create(name='guido', age=1)
    assert test_client.objects.get(pk=1).name == 'guido'

    user = test_client.objects.get(pk=1)
    assert user.age == 1

    user.age = 20
    assert user.age == 20

    test_client.objects.get(pk=1).delete()

