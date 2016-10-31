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
from networkx import NetworkXError
from structure.Graph import Graph
from structure.GPSGraph import GPSGraph
from structure.data_generator import generate_graph_from_file


class StructureTest(unittest.TestCase):
    def setUp(self):
        log.info("STARTING tests")

    def testStructure(self):
        graph = Graph(name='graph')

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        # Nodes
        self.assertTrue(graph.has_node('node0'))
        self.assertFalse(graph.has_node('node2'))

        self.assertEqual({'node0', 'node1'}, set(graph.nodes()))

        # Edges
        self.assertTrue(graph.has_edge('node0', 'node1'''))
        self.assertFalse(graph.has_edge('node1', 'node2'))
        self.assertFalse(graph.has_edge('node1', 'node0'))  # is directed graph
        self.assertEqual({'size': 3}, graph.get_edge_data('node0', 'node1'))
        self.assertIsNone(graph.get_edge_data('node1', 'node0'))
        self.assertEqual({'node0 --> node1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.edges())))
        self.assertEqual('node1', graph.successors_iter('node0').next())

        # remove
        self.assertRaises(NetworkXError, graph.remove_node, 'node2')
        graph.remove_node('node0')
        self.assertFalse(graph.has_node('node0'))
        self.assertFalse(graph.has_edge('node0', 'node1'))

    def testDrivers(self):
        graph = GPSGraph(name='graph')

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        # add drivers
        self.assertTrue(graph.addDriver('node0', 'node1', 0, nb=3))
        self.assertFalse(graph.addDriver('node0', 'node2', 2))

        # "has" assertions
        self.assertTrue(graph.hasStartingTime('node0', 'node1', 0))
        self.assertFalse(graph.hasDriver('node1', 'node0'))
        self.assertTrue(graph.hasDriver('node0', 'node1'))

        # "getAll" functions
        self.assertEqual(('node0', 'node1', 0, 3), graph.getAllDrivers().next())
        self.assertEqual(('node0', 'node1', 0, 3), graph.getAllDriversFromStartingNode('node0').next())
        self.assertEqual(('node0', 'node1', 0, 3), graph.getAllDriversToEndingNode('node1').next())

        # properties
        self.assertTrue(graph.setDriversProperty('node0', 'node1', 'names', {'first': 'first', 'last': 'last'},
                                                 starting_time=0))
        self.assertIsNone(graph.getDriversProperty('node0', 'node1', 'names'))
        self.assertEqual({'first': 'first', 'last': 'last'},
                         graph.getDriversProperty('node0', 'node1', 'names', starting_time=0))

        # remove
        self.assertTrue(graph.removeDriver('node0', 'node1', 0))
        self.assertTrue(graph.hasDriver('node0', 'node1'))
        self.assertTrue(graph.removeDriver('node0', 'node1', 0, nb=2))
        self.assertFalse(graph.hasDriver('node0', 'node1'))
        self.assertFalse(graph.removeDriver('node1', 'node0', 2))

    def testParser(self):
        graph = generate_graph_from_file('static/graph-test-0.graphml')

        # Nodes
        self.assertTrue(graph.has_node('n0'))
        self.assertFalse(graph.has_node('n2'))

        self.assertEqual({'n0', 'n1'}, set(graph.nodes()))

        # Edges
        self.assertTrue(graph.has_edge('n0', 'n1'))
        self.assertFalse(graph.has_edge('n1', 'n0'))
        self.assertFalse(graph.has_edge('n1', 'n0'))  # is directed graph
        self.assertIsNone(graph.get_edge_data('n1', 'n0'))
        self.assertEqual({'n0 --> n1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.edges())))
        for source, target in graph.edges():
            self.assertTrue(graph.get_edge_property(source, target, "distance"))
            self.assertGreater(float(graph.get_edge_property(source, target, "distance")), 0.0)

        # remove
        self.assertRaises(NetworkXError, graph.remove_node, 'n2')
        graph.remove_node('n0')
        self.assertFalse(graph.has_node('n0'))
        self.assertFalse(graph.has_edge('n0', 'n1'))

        # data
        self.assertEqual(graph.get_position('n0'), (457.0, 296.0))

    def testDjikstra(self):
        graph = generate_graph_from_file('static/djikstra-test.graphml', distance_default=1.0)

        self.assertEqual(('1', '6', '7'), graph.get_paths_from_to('1', '7').next())
        self.assertEqual({('1', '6', '7'), ('1', '4', '5', '7')},
                         set(graph.get_paths_from_to('1', '7', length=1)))
        self.assertEqual(set([('1', '6', '7'), ('1', '4', '5', '7'), ('1', '4', '5', '6', '7'),
                              ('1', '4', '3', '5', '7'), ('1', '4', '3', '5', '6', '7'),
                              ('1', '2', '3', '5', '7'), ('1', '2', '3', '5', '6', '7'),
                              ('1', '6', '2', '3', '5', '7')]),
                         set(graph.get_all_paths_without_cycle('1', '7')))


if __name__ == '__main__':
    unittest.main()
