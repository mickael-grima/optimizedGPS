# -*- coding: utf-8 -*-
# !/bin/env python

from optimizedGPS.logger import configure

configure()

import unittest
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS.data import RoadMapper
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
        self.assertEqual(nodes, set(graph.nodes()))

        # right edges
        for i in range(length):
            for j in range(width):
                source = 'n_%s_%s' % (i, j)
                for target in graph.successors_iter(source):
                    self.assertIn(target, ['n_%s_%s' % (i + 1, j), 'n_%s_%s' % (i, j + 1), 'n_%s_%s' % (i + 1, j + 1)])

        # distances
        for source, target in graph.edges():
            self.assertTrue(graph.get_edge_property(source, target, 'distance'))
            self.assertGreater(float(graph.get_edge_property(source, target, 'distance')), 0.0)

    def testRandomDrivers(self):
        length, width = random.randint(1, 10), random.randint(1, 10)
        graph = generate_grid_data(length=length, width=width, graph_name='test-graph')

        nb_drivers, av_drivers = random.randint(5, 20), random.randint(1, 5)
        drivers_graph = generate_random_drivers(graph, total_drivers=nb_drivers, av_drivers=av_drivers)

        # exactly nb_drivers drivers in graph
        self.assertEqual(nb_drivers, drivers_graph.number_of_drivers())

    def testOSMAPI(self):
        min_lat, min_lon, max_lat, max_lon = -1.55, 47.21, -1.549, 47.211
        rmapper = RoadMapper()
        graph = rmapper.get_graph(min_lon, min_lat, max_lon, max_lat)
        stats = graph.get_stats()

        self.assertGreater(stats['nodes'], 0)
        self.assertGreater(stats['edges'], 0)


if __name__ == '__main__':
    unittest.main()
