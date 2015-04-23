# -*- coding: utf-8 -*-

class QuerySet(object):
    def __init__(self, model, backend):
        self.model = model
        self.backend = backend

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
