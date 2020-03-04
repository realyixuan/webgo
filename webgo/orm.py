import sqlite3
from collections import abc

from webgo.exceptions import FieldError
from webgo.config import DB_FILE


class DBConnect:
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
        attrs['__mappings__'] = mappings
        attrs['__table__'] = name
        return type.__new__(mcs, name, bases, attrs)


class RecordSet(abc.Set):
    def __init__(self, iterable=None, model=None):
        if iterable:
            self._set = set(iterable)
        self.model = model

    def __get__(self, inst, class_):
        return self.__class__(model=class_)

    def query(self, **kwargs):
        # Return a recordset including all specific records of table
        if len(kwargs) > 1:
            raise KeyError('support search by one key word only')
        if not kwargs:
            kwargs[1] = 1
        kw = list(kwargs.keys())[0]
        cols = list(self.model.__mappings__.keys())
        cols.append('pk')
        colstr = ','.join(cols)
        with DBConnect() as conn:
            rows = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE {kw}=? 
                """, (kwargs[kw], )
                                ).fetchall()
        return self.__class__(self.model(**dict(zip(cols, row)))
                              for row in rows)

    def get(self, pk):
        # Return a single record
        cols = list(self.model.__mappings__.keys())
        cols.append('pk')
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
               % (self.model.__name__, ','.join(map(lambda x: x.pk, self._set)))


class Model(metaclass=ModelMetaclass):

    __abstract__ = True

    objects = RecordSet()

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @classmethod
    def create_table(cls, mname: str):
        """ Create a table in database
        :param mname: table model name
        """
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        for class_ in cls.__subclasses__():
            if mname == class_.__name__:
                model = class_
                break
        else:
            raise Exception(f'No {mname} table')

        try:
            cols = ','.join([f'{c.col_name} {c.col_type}' for c in model.__mappings__.values()])\
                   + f', pk INTEGER PRIMARY KEY AUTOINCREMENT'
            cur.execute(f"CREATE TABLE {model.__table__} ({cols})")
            table = model.__table__
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        else:
            print(f'{ table } created')
        finally:
            conn.close()

    def _create(self):
        cols = []
        args = []
        params = []
        for k, v in self.__mappings__.items():
            cols.append(v.col_name)
            args.append(self.__dict__[k])
            params.append('?')
        cols_str = ','.join(cols)
        params_str = ','.join(params)
        sql = f"""
            INSERT INTO { self.__table__ } ({ cols_str })
            VALUES ({ params_str })
        """
        with DBConnect() as conn:
            conn.execute(sql, tuple(args))

    def delete(self):
        sql = f"""
            DELETE FROM { self.__table__ }
            WHERE pk={self.pk}
        """
        with DBConnect() as conn:
            conn.execute(sql)

    def save(self):
        pk_value = self.__dict__.get('pk')
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
            args.append(self.__dict__[k])
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
        # Don't admit to assign value except fields' keys
        if key not in self.__mappings__:
            raise AttributeError(f"There's no column { key }")
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
    def __init__(self, col_name, col_type):
        self.col_name = col_name
        self.col_type = col_type


class IntegerField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'INT')


class TextField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'TEXT')


class User(Model):
    name = TextField('name')
    age = IntegerField('age')

