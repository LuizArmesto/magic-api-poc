# -*- coding: utf-8 -*-

import inspect

from ..utils import to_camelcase, to_underscore
from .queryset import QuerySet


def mapper(cls, datapackage, resource_name):
    resource = next((r for r in datapackage.resources
                     if r.name == resource_name))
    # Add some useful references
    cls.__datapackage_instance__ = datapackage
    cls.__resource__ = resource.name
    cls.__resource_instance__ = resource
    return cls


class Model(object):
    pass


class ModelsMaker(object):
    def __init__(self, datapackage, backend, prefix=None, base_class=Model):
        if isinstance(datapackage, basestring):
            datapackage = DataPackage(unicode(datapackage))
        self.datapackage = datapackage
        self.backend = backend
        self.prefix = prefix or self.datapackage.name
        self.base_class = base_class
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
            cls = self._create_class(resource)
            queryset_class = getattr(cls, '__queryset__')
            if queryset_class:
                cls.queryset = queryset_class(cls, self.backend)
            self._models[resource.name] = cls
        return self._models

    def populate(self, models=None):
        if models is None:
            models = self.models
        for model in models:
            self.backend.populate(model)

    def _create_class(self, resource):
        classname = to_camelcase(resource.name)

        attrs = {
            '__prefix__': self.prefix,
            '__datapackage__': self.datapackage,
            '__resource__': resource.name
        }
        attrs.update(self.backend.default_attrs)

        base = (self.backend.base_class, self.base_class)

        return type(classname, base, attrs)
