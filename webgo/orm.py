import sqlite3

from webgo.exceptions import FieldError
from webgo.config import DB_FILE


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if attrs.get('__abstract__'):
            return type.__new__(cls, name, bases, attrs)
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
        return type.__new__(cls, name, bases, attrs)


class RecordSet:
    def __init__(self, model=None):
        self.model = model

    def __get__(self, inst, class_):
        return self.__class__(class_)

    def get(self, pk):
        cols = list(self.model.__mappings__.keys())
        cols.append('pk')
        colstr = ','.join(cols)
        conn = sqlite3.connect(DB_FILE)
        with conn:
            row = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE pk={pk} 
                """).fetchone()
        conn.close()
        return self.model(**dict(zip(cols, row)))

    def all(self, **kwargs):
        if len(kwargs) > 1:
            raise KeyError('support search by one key word only')
        if not kwargs:
            kwargs[1] = 1
        kw = list(kwargs.keys())[0]
        cols = list(self.model.__mappings__.keys())
        cols.append('pk')
        colstr = ','.join(cols)
        conn = sqlite3.connect(DB_FILE)
        with conn:
            rows = conn.execute(f"""
                    SELECT {colstr} FROM {self.model.__table__}
                    WHERE {kw}=? 
                """, (kwargs[kw], )
                               ).fetchall()
        conn.close()
        return [self.model(**dict(zip(cols, row))) for row in rows]

    def create(self, **kwargs):
        cols = []
        args = []
        params = []
        for k, v in self.model.__mappings__.items():
            cols.append(v.col_name)
            args.append(kwargs[k])
            params.append('?')
        cols_str = ','.join(cols)
        params_str = ','.join(params)
        sql = f"""
            INSERT INTO { self.model.__table__ } ({ cols_str })
            VALUES ({ params_str })
        """
        conn = sqlite3.connect(DB_FILE)
        with conn:
            conn.execute(sql, tuple(args))
        conn.close()

    def _row(self):
        pass


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
            
    def delete(self):
        sql = f"""
            DELETE FROM { self.__table__ }
            WHERE pk={self.pk}
        """
        conn = sqlite3.connect(DB_FILE)
        with conn:
            conn.execute(sql)
        conn.close()

    def update(self):
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
        conn = sqlite3.connect(DB_FILE)
        with conn:
            conn.execute(sql, tuple(args))
        conn.close()

    def __getattr__(self, key):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no attribute { key }")

    def __setattr__(self, key, value):
        # Don't admit to assign value except fields' keys
        if key not in self.__mappings__:
            raise AttributeError(f"There's no column { key }")
        super().__setattr__(key, value)

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

