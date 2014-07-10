# -*- coding: utf-8 -*-

"""
    Tools mix
"""
from copy import deepcopy

__version__ = "$Id: util.py 218 2013-09-26 08:20:19Z campr $"

def dict_merge(a, b):
    """
    a can be overwritten by b
    """
    if not isinstance(b, dict):
        return b
    result = deepcopy(a)
    for k, v in b.iteritems():
        if k in result and isinstance(result[k], dict):
                result[k] = dict_merge(result[k], v)
        else:
            result[k] = deepcopy(v)
    return result
