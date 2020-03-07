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
    Model.create_table()
    return TestModel


def test_field_pk_id():
    with pytest.raises(FieldError):
        class User(Model):
            pk = IntegerField('pk')


def test_field_init(test_client):
    with pytest.raises(AttributeError):
        user = test_client(name='python', gender='male')
    with pytest.raises(TypeError):
        user = test_client(name='python', age='11')


def test_cduq(test_client):
    user1 = test_client(name='guido', age=1)
    user2 = test_client(name='linus', age=2)
    user3 = test_client(name='turing', age=3)
    user1.save()

    with pytest.raises(AttributeError):
        user1.pk = 2

    user1 = test_client.objects.get(pk=1)
    assert user1.name == 'guido'
    assert len(test_client.objects.query()) == 1

    assert user2.pk is None
    user2.save()
    assert user2.pk == 2

    user3.save()
    user2 = test_client.objects.get(pk=2)
    assert user2.age == 2

    all_user = test_client.objects.query()
    assert len(all_user) == 3
    assert user1 in all_user

    user1.delete()
    assert len(test_client.objects.query()) == 2

    all_user = test_client.objects.query()
    assert user1 not in all_user

