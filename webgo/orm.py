import sqlite3
import threading
import logging
from collections import abc

from webgo.exceptions import FieldError
from webgo import config

lock = threading.Lock()

logger = logging.getLogger(__name__)


class MyConnection(sqlite3.Connection):
    """
    Customize sql execute class on my behalf
    """
    def cursor(self, *args, **kwargs):
        return super().cursor(MyCursor)


class MyCursor(sqlite3.Cursor):
    def execute(self, *args, **kwargs):
        if len(args) == 1:
            return super().execute(*args, **kwargs)
        sql, values = args
        values = tuple(map(lambda x: None if isinstance(x, NewId) else x, values))
        return super().execute(sql, values)


class DBConnect:
    """ DB connection context manager """
    def __init__(self):
        self.conn = sqlite3.connect(
            database=config.DB_FILE,
            factory=MyConnection
        )

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        elif issubclass(exc_type, sqlite3.Error):
            self.conn.rollback()
            logger.warning(f'The DB operation error: {exc_val}', exc_info=True)
        else:
            logger.warning(f'Exception: {exc_val}', exc_info=True)
        self.conn.close()
        return True


class NewId:
    """ pseudo-id for new record """
    def __bool__(self):
        return False

    def __str__(self):
        return self.__class__.__name__


class ModelMetaclass(type):

    models = {}

    def __new__(mcs, name, bases, attrs):
        if attrs.get(f'_{name}__abstract'):
            attrs['__models__'] = mcs.models
            return type.__new__(mcs, name, bases, attrs)
        __fields__ = {}
        for k, v in attrs.items():
            if isinstance(v, Field):
                if k == 'pk':
                    raise FieldError("Can't define Field named 'pk'")
                v.col_name = k
                __fields__[k] = v

        __fields__['pk'] = Field(col_type='INTEGER PRIMARY KEY AUTOINCREMENT',
                                 col_name='pk')
        attrs['__fields__'] = __fields__
        attrs['__table__'] = name.lower()
        attrs['_pk'] = __fields__['pk']

        model = type.__new__(mcs, name, bases, attrs)
        mcs.models[name] = model
        return model


class RecordSet(abc.Set):
    """ Create a record set for result of query

    Cause of which it inherit abc.Set:
        We can perform some operations come from set.
            '|', '&', ... and so on

    Operations:
        >>> recset = MyModel.objects.query()
        >>> print(recest)
        <MyModel RecorcdSet (1,2,...)>

        >>> rec = MyModel.objects.get(pk=1)
        >>> print(rec)
        <Model:MyModel>


    """
    def __init__(self, iterable=None, model=None):
        if iterable:
            self._set = set(iterable)
        self.model = model

    def __get__(self, inst, class_):
        return self.__class__(model=class_)

    def query(self, **kwargs):
        """ Return a recordset including all specific records of table """
        if len(kwargs) > 1:
            raise KeyError('support search by one key word only')
        if not kwargs:
            kwargs[1] = 1
        kw = list(kwargs.keys())[0]
        cols = list(self.model.__fields__.keys())
        colstr = ','.join(cols)
        with DBConnect() as conn:
            rows = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE {kw}=? 
                """, (kwargs[kw], )
                                ).fetchall()
        return self.__class__(
            (self.model(**dict(zip(cols, row))) for row in rows),
            self.model
        )

    def get(self, pk):
        """ Return a single record """
        if pk is None:
            return None
        cols = list(self.model.__fields__.keys())
        colstr = ','.join(cols)
        with DBConnect() as conn:
            row = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE pk={pk} 
                """).fetchone()
        return self.model(**dict(zip(cols, row)))

    def _row(self):
        pass

    def __contains__(self, value):
        return value in self._set

    def __iter__(self):
        return iter(self._set)

    def __len__(self):
        return len(self._set)

    def __str__(self):
        return '<%s RecorcdSet (%s)>' % (self.model.__name__, ','.join(map(lambda x: str(x.pk), self._set)))

    __repr__ = __str__


class Model(metaclass=ModelMetaclass):
    """ Base class of all models mapping tables
    Define all abstract methods interact with DB

    class attrs:
        __abstract   : don't create table in DB if True
        __table__    : the name of relative table (which is lowercase of class name)
        __fields__   : dict that stores all models' field name-object paris
        __models__   : dict to store all name-class pairs of subclass of Model
    """
    __abstract = True

    objects = RecordSet()

    def __init__(self, **kwargs):
        # It can do initializing pk at here, but which is forbidden
        # So it may be problematic
        for key, value in kwargs.items():
            if key not in self.__fields__:
                raise AttributeError(f'{key} does not exist')
            if value is not None\
                    and not isinstance(value, self.__fields__[key].py_type):
                raise TypeError(f'{key} type is error')
        if 'pk' not in kwargs:
            pk = NewId()
            kwargs['pk'] = pk
        for k in self.__fields__:
            self.__fields__[k].__set__(self, kwargs.get(k))

    @classmethod
    def create_table(cls):
        """ Create a table in database
        It will create all tables through all base class's subclass
        """
        with DBConnect() as conn:
            get_tables = f"""
                SELECT NAME
                FROM sqlite_master
                WHERE type='table'
            """
            tables = set(
                map(lambda x: x[0], conn.execute(get_tables).fetchall())
            )

            if hasattr(cls, f'_{cls.__name__}__abstract'):
                models = cls.__subclasses__()
            else:
                models = [cls]

            for model in models:
                if model.__name__.lower() in tables:
                    continue
                cols = ','.join([f'{field.col_name} {field.col_type}'
                                 for field in model.__fields__.values()])
                conn.execute(f"CREATE TABLE {model.__table__} ({cols})")
                logger.info(f'Table {model.__table__} created')

    def _create(self):
        """ Create record by instance of class """
        cols = []
        args = []
        params = []
        for k, v in self.__fields__.items():
            cols.append(v.col_name)
            args.append(self.col_value[k])
            params.append('?')
        cols_str = ','.join(cols)
        params_str = ','.join(params)
        sql = f"""
            INSERT INTO { self.__table__ } ({ cols_str })
            VALUES ({ params_str })
        """
        with DBConnect() as conn:
            conn.execute(sql, tuple(args))
            pk = conn.execute(f"""
                select pk from {self.__table__} order by pk desc
            """).fetchone()
            self.__fields__['pk'].__set__(self, pk[0])

    def delete(self):
        with lock:
            sql = f"""
                DELETE FROM { self.__table__ }
                WHERE pk={self.pk}
            """
            with DBConnect() as conn:
                conn.execute(sql)
            self.__fields__['pk'].__set__(self, NewId())

    def save(self):
        with lock:
            pk_value = self.pk
            if pk_value:
                self._update()
            else:
                self._create()

    def _update(self):
        cols = []
        args = []
        params = []
        for k, v in self.__fields__.items():
            cols.append(v.col_name)
            args.append(self.col_value[k])
            params.append('?')
        cols_str = ','.join([col+'=?' for col in cols])
        sql = f"""
            update { self.__table__ } 
            set { cols_str }
            where pk={self.pk}
        """
        with DBConnect() as conn:
            conn.execute(sql, tuple(args))

    @property
    def pk(self):
        return self._pk

    @property
    def col_value(self):
        return self.__dict__

    def __getattr__(self, key):
        if key not in self.__fields__:
            raise AttributeError(f"There's no attribute { key }")

    def __setattr__(self, key, value):
        if key not in self.__fields__:
            raise FieldError(f"No such the field {key}")
        super().__setattr__(key, value)

    def __eq__(self, other):
        return hash(self) == hash(other) and self.__dict__ == other.__dict__

    def __hash__(self):
        return self.pk

    def __str__(self):
        return '<%s:%s # pk=%s>' % ('Model', self.__class__.__name__, self.pk)

    __repr__ = __str__


class Field:
    """ Base class of Field class """
    def __init__(self, col_type, col_name=None):
        self.col_type = col_type
        self.col_name = col_name
        self.py_type = {
            'text': str,
            'int': int,
            'many2one': int,
        }.get(col_type, object)

    def __get__(self, inst, class_):
        if inst is None:
            return self
        return inst.col_value[self.col_name]

    def __set__(self, inst, value):
        inst.col_value[self.col_name] = value


class IntegerField(Field):
    def __init__(self, **kwargs):
        super().__init__('int', **kwargs)


class TextField(Field):
    def __init__(self, **kwargs):
        super().__init__('text', **kwargs)


class Many2one(Field):
    def __init__(self, related_model, **kwargs):
        self.related_model = related_model
        super().__init__('many2one', **kwargs)

    def __get__(self, inst, class_):
        """
        issues:
            TODO: How to address problem get identical values repeatedly
                AND How to caching values
        """
        if inst is None:
            return self
        related_class = inst.__models__[self.related_model]
        value = inst.col_value[self.col_name]
        return related_class.objects.get(pk=value)


class One2many(Field):
    def __init__(self, related_model, related_field, **kwargs):
        self.related_model = related_model
        self.related_field = related_field
        super().__init__('one2many', **kwargs)

    def __get__(self, inst, class_):
        if inst is None:
            return self
        related_class = inst.__models__[self.related_model]
        return related_class.objects.query(**{self.related_field: inst.pk})

    def __set__(self, inst, class_):
        """ not permitted to evaluate One2many Field"""
        raise FieldError("One2many can't be assigned!")


class User(Model):
    name = TextField()
    age = IntegerField()
