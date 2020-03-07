import sqlite3
from collections import abc

from webgo.exceptions import FieldError
from webgo.config import DB_FILE


class DBConnect:
    """ DB connection context manager """
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        elif issubclass(exc_type, sqlite3.Error):
            self.conn.rollback()
            print(f'The DB operation error: {exc_val}')
        else:
            print(f'Exception: {exc_val}')
        self.conn.close()
        return True


class ModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        if attrs.get('__abstract__'):
            return type.__new__(mcs, name, bases, attrs)
        mappings = {}
        for k, v in attrs.items():
            if isinstance(v, _Field):
                if k == 'pk':
                    raise FieldError("Can't define Field named 'pk'")
                mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        mappings['pk'] = _Field('pk', 'INTEGER PRIMARY KEY AUTOINCREMENT')
        attrs['__mappings__'] = mappings
        attrs['__table__'] = name
        return type.__new__(mcs, name, bases, attrs)


class RecordSet(abc.Set):
    """ Create a record set for result of query

    Cause of which it inherit abc.Set:
        We can perform some operations come from set.
            '|', '&', ... and so on

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
        cols = list(self.model.__mappings__.keys())
        colstr = ','.join(cols)
        with DBConnect() as conn:
            rows = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE {kw}=? 
                """, (kwargs[kw], )
                                ).fetchall()
        return self.__class__(
            (self.model(**dict(zip(cols, row))) for row in rows), self.model)

    def get(self, pk):
        """ Return a single record which is a instance of class """
        cols = list(self.model.__mappings__.keys())
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
        return '<%s RecorcdSet (%s)>'\
               % (self.model.__name__,
                  ','.join(map(lambda x: str(x.pk), self._set)))


class Model(metaclass=ModelMetaclass):
    """ Base class of all models mapping tables
    Define all abstract methods interact with DB
    """
    __abstract__ = True

    objects = RecordSet()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in self.__mappings__:
                raise AttributeError(f'{key} does not exist')
            if not isinstance(value, self.__mappings__[key]._py_type):
                raise TypeError(f'{key} type is error')
        pk = None
        if 'pk' in kwargs:
            pk = kwargs.pop('pk')
        kwargs['_pk'] = pk
        self.__dict__.update(**kwargs)

    @property
    def pk(self):
        return self._pk

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
            for class_ in cls.__subclasses__():
                if class_.__name__ in tables:
                    continue
                cols = ','.join([f'{c.col_name} {c.col_type}'
                                 for c in class_.__mappings__.values()])
                conn.execute(f"CREATE TABLE {class_.__table__} ({cols})")
                print(f'Table {class_.__table__} created')

    def _create(self):
        """ Create record by instance of class """
        cols = []
        args = []
        params = []
        for k, v in self.__mappings__.items():
            cols.append(v.col_name)
            args.append(getattr(self, k))
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
            self._pk = pk[0]

    def delete(self):
        sql = f"""
            DELETE FROM { self.__table__ }
            WHERE pk={self.pk}
        """
        with DBConnect() as conn:
            conn.execute(sql)

    def save(self):
        pk_value = self.pk
        if pk_value:
            self._update()
        else:
            self._create()

    def _update(self):
        cols = []
        args = []
        params = []
        for k, v in self.__mappings__.items():
            cols.append(v.col_name)
            args.append(getattr(self, k))
            params.append('?')
        cols_str = ','.join([col+'=?' for col in cols])
        sql = f"""
            update { self.__table__ } 
            set { cols_str }
            where pk={self.pk}
        """
        with DBConnect() as conn:
            conn.execute(sql, tuple(args))

    def __getattr__(self, key):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no attribute { key }")

    def __setattr__(self, key, value):
        super().__setattr__(key, value)

    def __eq__(self, other):
        return hash(self) == hash(other) and self.__dict__ == other.__dict__

    def __hash__(self):
        return self.pk

    def __str__(self):
        return '<%s:%s>' % ('Model', self.__class__.__name__)

    def __repr__(self):
        return '<%s:%s # pk=%s>' % ('Model', self.__class__.__name__, self.pk)


class _Field:
    """ Base class of Field class """
    def __init__(self, col_name, col_type):
        self.col_name = col_name
        self.col_type = col_type
        self._py_type = {
            'TEXT': str,
            'INT': int,
        }.get(col_type, object)


class IntegerField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'INT')


class TextField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'TEXT')


class User(Model):
    name = TextField('name')
    age = IntegerField('age')

