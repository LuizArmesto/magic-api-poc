# -*- coding: utf-8 -*-

import os
import glob

from .backend import Backend

__all__ = ['Backend']

modules_names = [os.path.basename(f)[:-3] for f in
                 glob.glob(os.path.dirname(__file__) + '/*backend.py')]

# Import all modules from this package
for module in [module for module in modules_names]:
    __import__(module, locals(), globals())

# Get all `Backend` subclasses
backend_classes = {cls.__name__: cls for cls in Backend.__subclasses__()}
# Add subclasses references to locals
locals().update(backend_classes)

# For import *
__all__ += backend_classes.keys()

print 'Available data backends: {}'.format(', '.join(backend_classes.keys()))
