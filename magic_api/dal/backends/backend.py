# -*- coding: utf-8 -*-

class Backend(object):
    def populate(self, model):
        raise NotImplementedError()

    @property
    def default_attrs(self):
        return {}
