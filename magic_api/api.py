# -*- coding: utf-8 -*-

import datetime

from flask import Blueprint
from flask.ext import restful
from flask.ext.restful import fields as restful_fields
from flask.ext.restful.reqparse import RequestParser

from datapackage import DataPackage

from .db import ModelsMaker
from .utils import to_camelcase, to_underscore

# For import *
__all__ = ['magic_api', 'ResourcesMaker', 'add_resource']


API_PREFIX = "/api"


# Blueprint for MagicAPI
magic_api = Blueprint('magic_api', __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='/magic_api/static')

# Create the restful API
magic_api_base = restful.Api(magic_api, prefix=API_PREFIX)


class DateIso(restful_fields.Raw):

    def __init__(self, **kwargs):
        super(DateIso, self).__init__(**kwargs)

    def format(self, value):
        return value.isoformat()


# Map the data types between Data Package and Flask-Restiful fields
TYPES = {
    'string': {
        'default': restful_fields.String,
        'binary': None  # TODO
    },
    'number': {
        'default': restful_fields.Float
    },
    'integer': {
        'default': restful_fields.Integer
    },
    'boolean': {
        'default': restful_fields.Boolean
    },
    'null': {
        'default': restful_fields.Raw
    },
    'object': {
        'default': None  # TODO
    },
    'array': {
        'default': None  # TODO
    },
    'datetime': {
        'default': DateIso
    },
    'date': {
        'default': DateIso
    },
    'time': {
        'default': DateIso
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

# Resources types
SINGLE = 0
LIST = 1


def get_field_type(field):
    type_ = field.get('type')
    format_ = field.get('format', 'default')
    formats = TYPES.get(type_, {})
    return formats.get(format_) or formats.get('default')


def add_resource(cls, datapackage, resource_name, type_=LIST):
    datapackage_name = to_underscore(datapackage.name)
    resource_name = to_underscore(resource_name)
    url = '/{}/{}'.format(datapackage_name, resource_name)
    if type_ is SINGLE:
        url = '{}/<pk>'.format(url)
    print '---> {}{}'.format(API_PREFIX, url)
    magic_api_base.add_resource(cls, url)


class ResourcesMaker(object):
    def __init__(self, datapackage, session, metadata=None):
        if isinstance(datapackage, basestring):
            datapackage = DataPackage(unicode(datapackage))
        self.datapackage = datapackage
        self.session = session
        self.models_maker = ModelsMaker(datapackage, metadata=metadata)
        self._resources = {}

    @property
    def resources(self):
        if not self._resources:
            self.create_resources()
        return self._resources.values()

    def get_resource(self, name):
        if not self._resources:
            self.create_resources()
        return self._resources[name]

    def create_resources(self):
        self._resources = {}
        for resource_metadata in self.datapackage.resources:
            resource_name = resource_metadata.name
            model = self.models_maker.get_model(resource_name)
            list_, single = self._create_classes(model, resource_metadata)
            # List
            add_resource(list_, self.datapackage, resource_name, LIST)
            self._resources['{}List'.format(resource_name)] = list_
            # Single
            add_resource(single, self.datapackage, resource_name, SINGLE)
            self._resources[resource_name] = single
        return self._resources

    def _create_classes(self, model, resource_metadata):
        resource_name = resource_metadata.name
        classname = to_camelcase(resource_name)

        # Create Resource List class
        list_parser = RequestParser()
        # Expect pagination arguments
        list_parser.add_argument('page', type=int, default=0)
        list_parser.add_argument('per_page', type=int, default=100)

        session = self.session
        fields = {
            '_uid': restful_fields.Integer  # Internal id
        }
        for field in resource_metadata.schema.get('fields', []):
            # JSON properties names are camelCase
            property_name = to_camelcase(field.get('name'), False)
            # but SQLAlchemy columns are snake_case
            column_name = to_underscore(field.get('name'))
            # Add a filter argument for each column
            list_parser.add_argument(property_name, action='append')
            # Map JSON properties to SQLAlchemy columns
            args = []
            kwargs = {'attribute': column_name}
            fields[property_name] = get_field_type(field)(*args, **kwargs)

        def compile_query(query):
            from sqlalchemy.sql import compiler

            dialect = query.session.bind.dialect
            comp = compiler.SQLCompiler(dialect, query.statement)
            comp.compile()
            params = []
            for k in comp.positiontup:
                v = comp.params[k]
                if isinstance(v, unicode):
                    v = v.encode(dialect.encoding)
                params.append(v)
            return (comp.string.encode(dialect.encoding), tuple(params))

        @restful.marshal_with(fields)
        def get_list(self):
            model = self.__model__
            args = list_parser.parse_args()
            query = session.query(model)
            # Filters
            for field in resource_metadata.schema.get('fields', []):
                # JSON properties names are camelCase
                property_name = to_camelcase(field.get('name'), False)
                # but SQLAlchemy columns are snake_case
                column_name = to_underscore(field.get('name'))
                # Get the argument value from URL query, if any
                values = args[property_name]
                if values is not None:
                    query = query.filter(getattr(getattr(model, column_name), 'in_')(values))
            # Pagination
            query = query.offset(args['page'] * args['per_page'])
            query = query.limit(args['per_page'])

            print "*** Query ***\n\n", compile_query(query), '\n'
            # Filter
            result = query.all()
            return result

        list_ = type('{}List'.format(classname), (restful.Resource, ), {
            'get': get_list,
            '__resource_name__': resource_name,
            '__model__': model
        })

        # Create Resource Single class
        @restful.marshal_with(fields)
        def get_single(self, pk):
            query = session.query(self.__model__)
            result = query.get(pk)
            return result

        single = type(classname, (restful.Resource, ), {
            'get': get_single,
            '__resource_name__': resource_name,
            '__model__': model
        })

        return list_, single
