import sqlite3


_db_file = 'sqlite.db'


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
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
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)

    @classmethod
    def create_table(cls):
        try:
            conn = sqlite3.connect(_db_file)
            cur = conn.cursor()
            tables = []
            for model in cls.__subclasses__():
                table_name = model.__table__
                cols = ','.join(
                        [f'{ c.col_name } { c.col_type }' 
                           for c in model.__mappings__.values()]
                    )
                try:
                    cur.execute(f"create table { table_name } ({ cols })")
                    tables.append(table_name)
                except sqlite3.OperationalError:
                    pass
            conn.commit()
            print('create tables', '\n'.join(tables))
        finally:
            conn.close()

    def save(self):
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
            insert into { self.__table__ } ({ cols_str })
            values ({ params_str })
        """
        conn = sqlite3.connect(_db_file)
        cur = conn.cursor()
        try:
            cur.execute(sql, tuple(args))
            conn.commit()
        finally:
            conn.close()

    def __getattr__(self, key):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no attribute { key }")
        return self.__dict__.get(key, None)

    def __setattr__(self, key, value):
        if key not in self.__mappings__:
            raise AttributeError(f"There's no column { key }")
        self.__dict__[key] = value


class _Field:
    def __init__(self, col_name, col_type):
        self.col_name = col_name
        self.col_type = col_type

    def __str__(self):
        return '<%s:%s>' % (self.__class__.__name__, self.name)


class IntegerField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'INT')


class TextField(_Field):
    def __init__(self, col_name):
        super().__init__(col_name, 'TEXT')


class User(Model):
    id = IntegerField('id')
    name = TextField('name')

