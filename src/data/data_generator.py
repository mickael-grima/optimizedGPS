# -*- coding: utf-8 -*-
# !/bin/env python

# In this file we generate all kind of data: real one, random one, ...

from format_data import check_data_structure_format, check_data_format


class DataGenerator(object):
    structure = 'structure'
    drivers = 'drivers'

    @classmethod
    def get_basic_structure(cls):
        return {cls.structure: {}, cls.drivers: {}}

    @classmethod
    @check_data_structure_format
    def generate_grid_data(cls, length=5, width=5, **kwards):
        """ build a grid where the top-links node has name Node_0_0
            from a given node, the reachable nodes are the one to the right at the bottom
        """
        data = {cls.structure: {}}
        for i in range(length):
            for j in range(width):
                if i < length - 1:
                    if j < width - 1:
                        data['structure']['node_%s_%s' % (i, j)] = {
                            'node_%s_%s' % (i + 1, j): {
                                'size': kwards.get('size', 10)
                            },
                            'node_%s_%s' % (i, j + 1): {
                                'size': kwards.get('size', 10)
                            }
                        }
                    else:
                        data['structure']['node_%s_%s' % (i, j)] = {
                            'node_%s_%s' % (i + 1, j): {
                                'size': kwards.get('size', 10)
                            }
                        }
                else:
                    if j < width - 1:
                        data['structure']['node_%s_%s' % (i, j)] = {
                            'node_%s_%s' % (i, j + 1): {
                                'size': kwards.get('size', 10)
                            }
                        }

        return data

    @classmethod
    @check_data_format
    def add_drivers(cls, data, drivers):
        """ drivers = {driverName: {'start': ... , 'end': ...}}
        """
        data['drivers'] = drivers
        return data
