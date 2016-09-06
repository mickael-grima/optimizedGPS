# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

import logging
from logger import configure

configure()
log = logging.getLogger(__name__)

import unittest
from data.data_generator import DataGenerator


class DataTest(unittest.TestCase):
    def setUp(self):
        log.info("STARTING tests")

    def testGridData(self):
        data = DataGenerator.generate_grid_data(length=2, width=3, size=3)
        temp = {
            'structure': {
                'node_0_0': {
                    'node_1_0': {
                        'size': 3
                    },
                    'node_0_1': {
                        'size': 3
                    }
                },
                'node_1_0': {
                    'node_1_1': {
                        'size': 3
                    }
                },
                'node_0_1': {
                    'node_1_1': {
                        'size': 3
                    },
                    'node_0_2': {
                        'size': 3
                    }
                },
                'node_1_1': {
                    'node_1_2': {
                        'size': 3
                    }
                },
                'node_0_2': {
                    'node_1_2': {
                        'size': 3
                    }
                }
            }
        }
        self.assertDictEqual(temp, data)

        drivers = {
            'driver0': {
                'start': 'node_0_0',
                'end': 'node_1_2'
            },
            'driver1': {
                'start': 'node_0_1',
                'end': 'node_1_1'
            }
        }
        DataGenerator.add_drivers(data, drivers)
        self.assertDictEqual(data, {'structure': temp['structure'], 'drivers': drivers})


if __name__ == '__main__':
    unittest.main()
