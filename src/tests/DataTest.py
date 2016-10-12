# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

from logger import configure

configure()

import unittest
from data_generator import generate_grid_data, generate_random_drivers
import random


class DataTest(unittest.TestCase):

    def testGridGraph(self):
        """ Generate a grid graph with length and width random btw 1 and 10
            check if the strucure and the properties we want are here
        """
        length, width = random.randint(1, 10), random.randint(1, 10)
        graph = generate_grid_data(length=length, width=width, graph_name='test-graph')

        # nodes have the right name
        nodes = set(['n_%s_%s' % (i, j) for i in range(length) for j in range(width)])
        self.assertEqual(nodes, set(graph.getAllNodes()))

        # right edges
        for i in range(length):
            for j in range(width):
                source = 'n_%s_%s' % (i, j)
                for target in graph.getSuccessors(source):
                    self.assertIn(target, ['n_%s_%s' % (i + 1, j), 'n_%s_%s' % (i, j + 1), 'n_%s_%s' % (i + 1, j + 1)])

        # distances
        for source, target in graph.getAllEdges():
            self.assertTrue(graph.getEdgeProperty(source, target, 'distance'))
            self.assertGreater(float(graph.getEdgeProperty(source, target, 'distance')), 0.0)

    def testRandomDrivers(self):
        length, width = random.randint(1, 10), random.randint(1, 10)
        graph = generate_grid_data(length=length, width=width, graph_name='test-graph')

        nb_drivers, av_drivers = random.randint(5, 20), random.randint(1, 5)
        graph = generate_random_drivers(graph, total_drivers=nb_drivers, av_drivers=av_drivers)

        # exactly nb_drivers drivers in graph
        self.assertEqual(nb_drivers, graph.countDrivers())


if __name__ == '__main__':
    unittest.main()
