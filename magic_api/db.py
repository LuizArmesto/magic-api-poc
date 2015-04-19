# -*- coding: utf-8 -*-

import sqlalchemy
import sqlalchemy.orm
from datapackage import DataPackage

from .utils import to_camelcase, to_underscore

# For import *
__all__ = ['ModelsMaker', 'populate', 'mapper', 'Base']


# Map the data types between Data Package and SQLAlchemy
TYPES = {
    'string': {
        'default': sqlalchemy.types.String,
        'binary': sqlalchemy.types.LargeBinary
    },
    'number': {
        'default': sqlalchemy.types.Numeric
    },
    'integer': {
        'default': sqlalchemy.types.Integer
    },
    'boolean': {
        'default': sqlalchemy.types.Boolean
    },
    'null': {
        'default': sqlalchemy.types.NullType
    },
    'object': {
        'default': None  # TODO
    },
    'array': {
        'default': None  # TODO
    },
    'datetime': {
        'default': sqlalchemy.types.DateTime
    },
    'date': {
        'default': sqlalchemy.types.Date
    },
    'time': {
        'default': sqlalchemy.types.Time
    },
    'geopoint': {
        'default': None  # TODO
    },
    'geojson': {
        'default': None  # TODO
    },
    'any': {
        'default': None  # TODO
    }
}


def get_column_type(field):
    type_ = field.get('type')
    format_ = field.get('format', 'default')
    formats = TYPES.get(type_, {})
    return formats.get(format_) or formats.get('default')


def _create_table(resource, metadata, tablename):
    schema = resource.schema

    columns = [
        # Create an internal id to guarantee that there is
        # at least one primary key
        sqlalchemy.Column('_uid',  # Internal id
                          sqlalchemy.types.Integer,
                          primary_key=True,
                          autoincrement=True)
    ]
    # Iterate through fields to create a column to each one
    for field in schema.get('fields', []):
        column_type = get_column_type(field)
        column_name = to_underscore(field.get('name'))
        # TODO: Check if the field is a primary key or a foreign key
        column = sqlalchemy.Column(column_name, column_type)
        columns.append(column)

    return sqlalchemy.Table(tablename, metadata, *columns)


def populate(session, model):
    engine = session.get_bind(mapper=None)
    table = getattr(model, '__table__')
    # TODO: Raise an exception if there is no table defined
    # Make sure the table is created before inserting data
    table.create(engine, checkfirst=True)
    # Get references inserted by `mapper`
    datapackage = getattr(model, '__datapackage_instance__')
    resource = getattr(model, '__resource_instance__')
    data = datapackage.get_data(resource)
    # Using SQLAlchemy Core insert method for performance reason.
    # See: http://docs.sqlalchemy.org/en/rel_1_0/faq/performance.html
    engine.execute(model.__table__.insert(),
                   [{to_underscore(key): val for key, val in item.iteritems()}
                    for item in data])


# Default SQLALchemy metadata object
metadata_ = sqlalchemy.MetaData()


def mapper(cls, datapackage, resource_name, metadata=None):
    if metadata is None:
        metadata = metadata_
    resource = next((r for r in datapackage.resources
                     if r.name == resource_name))
    # Create SQLAlchemy table
    tablename = getattr(cls, '__tablename__', to_underscore(resource.name))
    table = _create_table(resource, metadata, tablename)
    # Add some useful references
    cls.__table__ = table
    cls.__datapackage_instance__ = datapackage
    cls.__resource__ = resource.name
    cls.__resource_instance__ = resource
    # Associate SQLAlchemy table with the class
    sqlalchemy.orm.mapper(cls, table)


class BaseMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super(BaseMeta, mcls).__new__(mcls, name, bases, attrs)
        datapackage = attrs.get('__datapackage__')
        if datapackage:
            if isinstance(datapackage, basestring):
                datapackage = DataPackage(unicode(datapackage))
            resource_name = unicode(attrs.get('__resource__'))
            if not hasattr(cls, '__tablename__'):
                tablename = '_'.join([datapackage.name, resource_name])
                attrs.update({
                    '__tablename__': to_underscore(tablename)
                })
            metadata = attrs.get('__metadata__')
            mapper(cls, datapackage, resource_name, metadata)
        return cls


class Base(object):
    __metaclass__ = BaseMeta

    def __init__(self, **kwargs):
        for (name, value) in kwargs.iteritems():
            attr_name = to_underscore(name)
            # FIXME: Check if attr_name is a column and not simply an attribute
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)


class ModelsMaker(object):
    def __init__(self, datapackage, session=None, table_prefix=None,
                 base_class=object, metadata=None):
        if isinstance(datapackage, basestring):
            datapackage = DataPackage(unicode(datapackage))
        self.datapackage = datapackage
        self.session = session
        self.table_prefix = table_prefix or self.datapackage.name
        self.base_class = base_class
        self.metadata = metadata
        self._models = {}

    @property
    def models(self):
        if not self._models:
            self.create_models()
        return self._models.values()

    def get_model(self, name):
        if not self._models:
            self.create_models()
        return self._models[name]

    def create_models(self):
        self._models = {}
        for resource in self.datapackage.resources:
            self._models[resource.name] = self._create_class(resource)
        return self._models

    def populate(self, session=None, models=None):
        if session is None:
            session = self.session
        if models is None:
            models = self.models
        for model in models:
            populate(session, model)

    def _create_class(self, resource):
        classname = to_camelcase(resource.name)
        tablename = '_'.join([self.table_prefix, resource.name])

        return type(classname, (Base, self.base_class), {
            # Add some references to be used by `BaseMeta` and `mapper`
            '__tablename__': to_underscore(tablename),
            '__datapackage__': self.datapackage,
            '__resource__': resource.name,
            '__metadata__': self.metadata
        })


def example():
    """Exemplo usando ModelsMaker, que cria um model para cada resource."""
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    modelsMaker = ModelsMaker('http://data.okfn.org/data/cpi/')
    modelsMaker.populate(session=session)
    Cpi = modelsMaker.get_model('cpi')
    print [(i.cpi, i.country_code, i.year)
           for i in session.query(Cpi).filter(Cpi.country_code == 'BRA').all()]


def example2():
    """Exemplo declarando um model explicitamente para um resource."""
    engine = sqlalchemy.create_engine('sqlite:///:memory:')
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    class Cpi(Base):
        __datapackage__ = 'http://data.okfn.org/data/cpi/'
        __resource__ = 'cpi'

    populate(session, Cpi)
    print [(i.cpi, i.country_code, i.year)
           for i in session.query(Cpi).filter(Cpi.country_code == 'BRA').all()]


if __name__ == '__main__':
    example()
