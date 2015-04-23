# -*- coding: utf-8 -*-

import sqlalchemy
import sqlalchemy.orm
from datapackage import DataPackage

from .backend import Backend as BaseBackend
from ..queryset import QuerySet as BaseQuerySet
from ..model import mapper as basemapper
from ...utils import to_camelcase, to_underscore, get_resource_by_name
from ...utils import get_type as get_column_type


# For import *
__all__ = ['populate', 'mapper', 'Base', 'QuerySet', 'Backend']


# Default SQLALchemy metadata object
metadata_ = sqlalchemy.MetaData()


class BaseMeta(type):
    def __new__(mcls, name, bases, attrs):
        cls = super(BaseMeta, mcls).__new__(mcls, name, bases, attrs)
        datapackage = attrs.get('__datapackage__')
        if datapackage:
            if isinstance(datapackage, basestring):
                datapackage = DataPackage(unicode(datapackage))
            resource_name = unicode(attrs.get('__resource__'))
            metadata = attrs.get('__metadata__', metadata_)
            mapper(cls, datapackage, resource_name, metadata)
            cls.__queryset__ = SQLAlchemyQuerySet
        return cls


class Base(object):
    __metaclass__ = BaseMeta

    def __init__(self, **kwargs):
        for (name, value) in kwargs.iteritems():
            attr_name = to_underscore(name)
            # FIXME: Check if attr_name is a column and not simply an attribute
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)


class SQLAlchemyBackend(BaseBackend):
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

    base_class = Base

    def __init__(self, session, metadata=None):
        if metadata is None:
            metadata = sqlalchemy.MetaData()
        self.session = session
        self.metadata = metadata

    @property
    def default_attrs(self):
        return {'__metadata__': self.metadata}

    def populate(self, model):
        populate(model, self.session)

Backend = SQLAlchemyBackend


class SQLAlchemyQuerySet(BaseQuerySet):
    def __init__(self, model, backend, sqla_query=None):
        if sqla_query is None:
            sqla_query = backend.session.query(model)
        super(SQLAlchemyQuerySet, self).__init__(model, backend)
        self._sqla_query = sqla_query

    def get(self, key):
        return self._sqla_query.get(key)

    def filter(self, *args, **kwargs):
        sqla_query = self._sqla_query.filter_by(**kwargs)
        return SQLAlchemyQuerySet(self.model, self.backend, sqla_query)

    def in_(self, *args, **kwargs):
        sqla_query = self._sqla_query
        for column_name, values in kwargs.items():
            column = getattr(self.model, column_name)
            sqla_query = self._sqla_query.filter(getattr(column, 'in_')(values))
        return SQLAlchemyQuerySet(self.model, self.backend, sqla_query)

    def limit(self, value):
        sqla_query = self._sqla_query.limit(value)
        return SQLAlchemyQuerySet(self.model, self.backend, sqla_query)

    def offset(self, value):
        sqla_query = self._sqla_query.offset(value)
        return SQLAlchemyQuerySet(self.model, self.backend, sqla_query)

    def all(self):
        return self._sqla_query.all()

QuerySet = SQLAlchemyQuerySet


def _create_sqla_table(resource, metadata, tablename):
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
        column_type = get_column_type(SQLAlchemyBackend.TYPES, field)
        column_name = to_underscore(field.get('name'))
        # TODO: Check if the field is a primary key or a foreign key
        column = sqlalchemy.Column(column_name, column_type)
        columns.append(column)

    return sqlalchemy.Table(tablename, metadata, *columns)


def populate(model, session):
    engine = session.get_bind(mapper=None)
    table = getattr(model, '__table__')
    # TODO: Raise an exception if there is no table defined
    # Make sure the table is created before inserting data
    table.create(engine, checkfirst=True)
    # Get references inserted by `mapper`
    datapackage = getattr(model, '__datapackage_instance__')
    resource = getattr(model, '__resource_instance__')
    # TODO: Raise an exception if there is no datapackage defined
    data = datapackage.get_data(resource)
    # Using SQLAlchemy Core insert method for performance reason.
    # See: http://docs.sqlalchemy.org/en/rel_1_0/faq/performance.html
    engine.execute(model.__table__.insert(),
                   [{to_underscore(key): val for key, val in item.iteritems()}
                    for item in data])


def mapper(cls, datapackage, resource_name, metadata=None):
    if metadata is None:
        metadata = metadata_
    cls = basemapper(cls, datapackage, resource_name)
    resource = get_resource_by_name(datapackage, resource_name)
    # Create SQLAlchemy table
    if not hasattr(cls, '__tablename__'):
        prefix = getattr(cls, '__prefix__', datapackage.name)
        tablename = '_'.join([prefix, resource_name])
        cls.__tablename__ = to_underscore(tablename)
    table = _create_sqla_table(resource, metadata, cls.__tablename__)
    cls.__table__ = table
    # Associate SQLAlchemy table with the class
    sqlalchemy.orm.mapper(cls, table)
    return cls
