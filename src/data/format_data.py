# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from logger import configure
from exceptions import MissingKeysError, StructureError, WrongDataError

configure()
log = logging.getLogger(__name__)

"""
The data should be a dictionnary with the following keys:
    {
        'structure': {
            node1: {
                node2: {
                    properties,
                    ...
                }
            }
        },
        'drivers': {
            'driverName': {
                start: ... ,
                end: ... ,
                ...
            }
        }
    }
"""


def check_data_structure_format(func):
    def check_format(*options, **kwards):
        data = func(*options, **kwards)
        # check if data is a dictionnary
        if not isinstance(data, dict):
            log.error('Data has the wrong type: %s instead of dict', type(data))
            raise TypeError('Data has the wrong type: %s instead of dict' % type(data))
        # Check if the key structure is in data
        if 'structure' not in data:
            log.error('Keys missing in data')
            raise MissingKeysError('Key "structure" missing in data')
        if not isinstance(data['structure'], dict):
            log.error('data.structure has the wrong type: %s instead of dict', type(data['structure']))
            raise TypeError('data.structure has the wrong type: %s instead of dict' % type(data['structure']))
        # for 'structure' associated value, we should have {node1: {node2 {properties}}} structure
        for source, dct in data['structure'].iteritems():
            if not isinstance(dct, dict):
                log.error('Structure error in data')
                raise StructureError('Structure error in data')
            for target, properties in data.iteritems():
                if not isinstance(properties, dict):
                    log.error('Structure error in data')
                    raise StructureError('Structure error in data')
        return data
    return check_format


def check_data_drivers_format(func):
    def check_format(*options, **kwards):
        data = func(*options, **kwards)
        # Check if key 'drivers' is in data
        if 'drivers' not in data:
            log.error('Keys missing in data')
            raise MissingKeysError('Key "structure" missing in data')
        if not isinstance(data['drivers'], dict):
            log.error('data.drivers has the wrong type: %s instead of dict', type(data['drivers']))
            raise TypeError('data.drivers has the wrong type: %s instead of dict' % type(data['drivers']))
        # for drivers, we should have {'driverName': {'start': ... , 'end': ..., ...}} structures
        for name, props in data['drivers'].iteritems():
            if not isinstance(props, dict):
                log.error('Structure error in data')
                raise StructureError('Structure error in data')
            if 'start' not in props and 'end' not in props:
                log.error('Keys missing in data')
                raise MissingKeysError('Keys missing in data')
        return data
    return check_format


def check_data_format(func):
    @check_data_structure_format
    @check_data_drivers_format
    def check_format(*options, **kwards):
        data = func(*options, **kwards)
        # start and end nodes should exist in the structure data
        for name, props in data['drivers'].iteritems():
            if props['start'] not in data['structure']:
                log.error("Start of a driver doesn't exist in the graph")
                raise WrongDataError("Start of a driver doesn't exist in the graph")
            if props['end'] not in [target for dct in data['structure'].itervalues() for target in dct.iterkeys()]:
                log.error("End %s of a driver doesn't exist in the graph", props['end'])
                raise WrongDataError("End %s of a driver doesn't exist in the graph" % props['end'])
        return data
    return check_format
