import sqlite3


_db_file = 'sqlite.db'


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if attrs.get('__abstract__'):
            return type.__new__(cls, name, bases, attrs)
        mappings = {}
        for k, v in attrs.items():
            if isinstance(v, _Field):
                mappings[k] = v
        for k in mappings.keys():
            attrs.pop(k)
        attrs['__mappings__'] = mappings
        attrs['__table__'] = name
        return type.__new__(cls, name, bases, attrs)


class Model(metaclass=ModelMetaclass):

    __abstract__ = True

    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @classmethod
    def create_table(cls, mname):
        conn = sqlite3.connect(_db_file)
        cur = conn.cursor()
        for class_ in cls.__subclasses__():
            if mname == class_.__name__:
                model = class_
                break
        else:
            raise Exception(f'No { mname } table')

        try:
            cols = ','.join(
                    [f'{ c.col_name } { c.col_type }'
                       for c in model.__mappings__.values()]
            )
            cur.execute(f"CREATE TABLE { model.__table__ } ({ cols })")
            table = model.__table__
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        else:
            print(f'{ table } created')
        finally:
            conn.close()
            
    @classmethod
    def query(cls, **kwargs):
        if len(kwargs) > 1:
            raise KeyError('support search by one key word only')
        kw = list(kwargs.keys())[0]
        cols = list(cls.__mappings__.keys())
        colstr = ','.join(cols)
        conn = sqlite3.connect(_db_file)
        with conn:
            res = conn.execute(f"""
                    SELECT { colstr } FROM { cls.__table__ }
                    WHERE { kw }=? 
                """, (kwargs[kw], )
                ).fetchone()
        conn.close()
        return cls(**dict(zip(cols, res)))

    def delete(self):
        sql = f"""
            DELETE FROM { self.__table__ }
            WHERE id={ self.id }
        """
        conn = sqlite3.connect(_db_file)
        with conn:
            conn.execute(sql)
        conn.close()

    def create(self):
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
        conn = sqlite3.connect(_db_file)
        with conn:
            conn.execute(sql, tuple(args))
        conn.close()

    def write(self):
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
            where { self.id } = ?
        """
        conn = sqlite3.connect(_db_file)
        with conn:
            conn.execute(sql, tuple(args+[self.id]))
        conn.close()

    def __getattr__(self, key):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no attribute { key }")
        return self.__dict__.get(key, None)

    def __setattr__(self, key, value):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no column { key }")
        self.__dict__[key] = value

    def __str__(self):
        return '<%s:%s>' % ('Model', self.__class__.__name__)


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
    id = IntegerField('id')
    name = TextField('name')

