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
from structure.GPSGraph import GPSGraph
from data_generator import generate_graph_from_file


class StructureTest(unittest.TestCase):
    def setUp(self):
        log.info("STARTING tests")

    def testStructure(self):
        graph = GPSGraph(name='graph')

        graph.addNode('node0')
        graph.addNode('node1')
        graph.addEdge('node0', 'node1', size=3)

        # Nodes
        self.assertTrue(graph.hasNode('node0'))
        self.assertFalse(graph.hasNode('node2'))

        self.assertEqual({'node0', 'node1'}, set(graph.getAllNodes()))

        # Edges
        self.assertTrue(graph.hasEdge('node0', 'node1'''))
        self.assertFalse(graph.hasEdge('node1', 'node2'))
        self.assertFalse(graph.hasEdge('node1', 'node0'))  # is directed graph
        self.assertEqual({'size': 3}, graph.getEdgeProperties('node0', 'node1'))
        self.assertIsNone(graph.getEdgeProperties('node1', 'node0'))
        self.assertEqual({'node0 --> node1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.getAllEdges())))
        self.assertEqual('node1', graph.getSuccessors('node0').next())

        # remove
        self.assertFalse(graph.removeNode('node2'))
        self.assertTrue(graph.removeNode('node0'))
        self.assertFalse(graph.hasNode('node0'))
        self.assertFalse(graph.hasEdge('node0', 'node1'))

    def testDrivers(self):
        graph = GPSGraph(name='graph')

        graph.addNode('node0')
        graph.addNode('node1')
        graph.addEdge('node0', 'node1', size=3)

        self.assertTrue(graph.addDriver('node0', 'node1'))
        self.assertFalse(graph.addDriver('node0', 'node2'))
        self.assertFalse(graph.hasDriver('node1', 'node0'))
        self.assertTrue(graph.hasDriver('node0', 'node1'))
        self.assertEqual((('node0', 'node1'), 1), graph.getAllDrivers().next())
        self.assertEqual((('node0', 'node1'), 1), graph.getAllDriversFromStartingNode('node0').next())
        self.assertEqual((('node0', 'node1'), 1), graph.getAllDriversToEndingNode('node1').next())
        self.assertTrue(graph.removeDriver('node0', 'node1'))
        self.assertFalse(graph.hasDriver('node0', 'node1'))
        self.assertFalse(graph.removeDriver('node1', 'node0'))

    def testParser(self):
        graph = generate_graph_from_file('static/graph-test.graphml')

        # Nodes
        self.assertTrue(graph.hasNode('n0'))
        self.assertFalse(graph.hasNode('n2'))

        self.assertEqual({'n0', 'n1'}, set(graph.getAllNodes()))

        # Edges
        self.assertTrue(graph.hasEdge('n0', 'n1'))
        self.assertFalse(graph.hasEdge('n1', 'n0'))
        self.assertFalse(graph.hasEdge('n1', 'n0'))  # is directed graph
        self.assertIsNone(graph.getEdgeProperties('n1', 'n0'))
        self.assertEqual({'n0 --> n1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.getAllEdges())))

        # remove
        self.assertFalse(graph.removeNode('n2'))
        self.assertTrue(graph.removeNode('n0'))
        self.assertFalse(graph.hasNode('n0'))
        self.assertFalse(graph.hasEdge('n0', 'n1'))

        # data
        self.assertEqual(graph.getData('n0'), {'geometry': {'x': '457.0', 'y': '296.0'}})

    def testDjikstra(self):
        graph = generate_graph_from_file('static/djikstra-test.graphml')
        for source, target in graph.getAllEdges():
            graph.setEdgeProperty(source, target, 'distance', 1)

        self.assertEqual(('n0', 'n6', 'n1'), graph.getPathsFromTo('n0', 'n1').next())
        self.assertEqual({('n0', 'n6', 'n1'), ('n0', 'n4', 'n5', 'n1')},
                         set(graph.getPathsFromTo('n0', 'n1', length=3)))


if __name__ == '__main__':
    unittest.main()
