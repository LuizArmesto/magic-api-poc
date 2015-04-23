# -*- coding: utf-8 -*-

from .backend import Backend as BaseBackend
from ..queryset import QuerySet as BaseQuerySet


# For import *
__all__ = ['populate', 'mapper', 'Base', 'QuerySet', 'Backend']


class Base(object):
    pass


class PandasBackend(BaseBackend):
    TYPES = {}

    def populate(self, model):
        raise NotImplementedError()

Backend = PandasBackend


class PandasQuerySet(BaseQuerySet):
    def get(self, key):
        raise NotImplementedError()

    def filter(self, **kwargs):
        raise NotImplementedError()

    def in_(self, **kwargs):
        raise NotImplementedError()

    def limit(self, value):
        raise NotImplementedError()

    def offset(self, value):
        raise NotImplementedError()

    def all(self):
        raise NotImplementedError()

QuerySet = PandasQuerySet


def populate(model):
    pass


def mapper(cls, datapackage, resource_name):
    pass
