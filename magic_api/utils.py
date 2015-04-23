# -*- coding: utf-8 -*-

import unicodedata

# For import *
__all__ = ['normalize_name', 'to_camelcase', 'to_underscore']


def normalize_name(value):
    value = unicodedata.normalize('NFKD', unicode(value)).encode('ascii', 'ignore')
    return ''.join(c for c in value
                   if c.isalnum() or c.isspace() or c in ['_', '-'])


def to_camelcase(value, uppercase_first_letter=True):
    value = normalize_name(value)
    result = ''.join(c for c in value.title().strip() if not c.isspace())
    if not uppercase_first_letter:
        result = '{}{}'.format(result[0].lower(), result[1:])
    return result


def to_underscore(value):
    value = normalize_name(value)
    return value.lower().strip().replace(' ', '_').replace('-', '_')


def get_type(types, field):
    type_ = field.get('type')
    format_ = field.get('format', 'default')
    formats = types.get(type_, {})
    return formats.get(format_) or formats.get('default')


def get_resource_by_name(datapackage, resource_name):
    return next((r for r in datapackage.resources if r.name == resource_name))
