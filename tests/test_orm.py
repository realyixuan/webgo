"""
Usage:
    $ python -m unittest tests/test_orm.py
"""

import os
import unittest
import tempfile
import logging

from collections.abc import Iterable, Iterator

from webgo import config
from webgo import orm

from webgo.exceptions import FieldError
from webgo.orm import (
    Model, IntegerField, TextField, Many2one, User, NewId,
    One2many,
)

# orm.logger.disabled = True
logging.disable(logging.CRITICAL)

ORIGINAL_DB_PATH = config.DB_FILE


def setUpModule():
    pass


def tearDownModule():
    pass


class RegularTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class DemoModel(Model):
            name = TextField()
            age = IntegerField()

        cls.model = DemoModel

    @classmethod
    def tearDownclass(cls):
        config.DB_FILE = ORIGINAL_DB_PATH

    def setUp(self):
        self.dir = dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(dir.name, 'sqlite.db')
        config.DB_FILE = db_path
        self.model.create_table()

        self.demo = demo = self.model(name='Guido', age=65)
        demo.save()

    def tearDown(self):
        self.dir.cleanup()

    def test_field_pk_id_defined(self):
        try:
            class _(Model):
                pk = IntegerField()
        except FieldError:
            pass
        else:
            self.fail("Did not raise FieldError")

    def test_field_init_error(self):
        self.assertRaises(
            AttributeError,
            self.model,
            nickname='Guido',
            age=65
        )
        self.assertRaises(
            TypeError,
            self.model,
            name='Guido',
            age='65'
        )

    def test_init_attr(self):
        demo = self.model(name='BDFL', age=65)
        self.assertEqual(demo.name, 'BDFL')
        self.assertEqual(demo.age, 65)
        self.assertTrue(isinstance(demo.pk, NewId))

    def test_create(self):
        self.assertEqual(self.demo.pk, 1)

    def test_read(self):
        self.assertEqual(self.demo.name, 'Guido')

    def test_delete(self):
        self.demo.delete()
        self.assertTrue(isinstance(self.demo.pk, NewId))
        recs = self.model.objects.query()
        self.assertEqual(len(recs), 0)


class Many2oneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Exam(Model):
            nickname = TextField()
            grade = IntegerField()
            user = Many2one(related_model="User")

        cls.exam_model = Exam

    @classmethod
    def tearDownclass(cls):
        config.DB_FILE = ORIGINAL_DB_PATH

    def setUp(self):
        self.dir = dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(dir.name, 'sqlite.db')
        config.DB_FILE = db_path
        self.exam_model.create_table()
        User.create_table()
        self.user = User(name='Guido', age=65)
        self.user.save()

    def tearDown(self):
        self.dir.cleanup()

    def test_many2one_init(self):
        exam = self.exam_model(nickname='Guido', grade=80)
        self.assertEqual(exam.user, None)
        exam.user = self.user.pk
        self.assertEqual(exam.user.pk, self.user.pk)

    def test_many2one_save(self):
        exam = self.exam_model(nickname='Guido', grade=80, user=self.user.pk)
        exam.save()
        self.assertEqual(exam.user.pk, self.user.pk)

class One2manyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class Exam(Model):
            grade = IntegerField()
            person_id = Many2one(related_model="Person")

        class Person(Model):
            name = TextField()
            grade_ids = One2many('Exam', 'person_id')

        cls.exam_model = Exam
        cls.person_model = Person

    @classmethod
    def tearDownclass(cls):
        config.DB_FILE = ORIGINAL_DB_PATH

    def setUp(self):
        self.dir = dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(dir.name, 'sqlite.db')
        config.DB_FILE = db_path

        self.exam_model.create_table()
        self.person_model.create_table()

        self.person = self.person_model(name='Guido')
        self.person.save()

    def tearDown(self):
        self.dir.cleanup()

    def test_one2many(self):
        self.exam_model(grade=80, person_id=self.person.pk).save()
        self.exam_model(grade=80, person_id=self.person.pk).save()

        grade_set = set()
        for grade_id in self.person.grade_ids:
            grade_set.add(grade_id.pk)

        self.assertEqual(grade_set, {1, 2})

