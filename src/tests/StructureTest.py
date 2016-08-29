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
from structure.CongestionGPSGraph import CongestionGPSGraph
from structure.Node import Node


class StructureTest(unittest.TestCase):
    def setUp(self):
        log.info("STARTING tests")

    def testBuild(self):
        graph = GPSGraph(name='graph')

        node0 = Node(name='node0')
        node1 = Node(name='node1')
        node2 = Node(name='node2')

        graph.addNode(node0)
        graph.addNode(node1)
        graph.addEdge(node0, node1)

        # Nodes
        self.assertTrue(graph.hasNode(node0))
        self.assertFalse(graph.hasNode(node2))

        self.assertIn(node0, [n for n in graph.getNodesByName('node0')])
        self.assertNotIn(node1, [n for n in graph.getNodesByName('node0')])
        self.assertEqual(set([node0, node1]), graph.getAllNodes())

        # Edges
        self.assertTrue(graph.hasEdge(node0, node1))
        self.assertFalse(graph.hasEdge(node1, node2))
        self.assertFalse(graph.hasEdge(node1, node0))  # is directed graph
        self.assertEqual('node0 --> node1', graph.getEdge(node0, node1).name)
        self.assertIsNone(graph.getEdge(node1, node0))
        self.assertEqual(set(['node0 --> node1']), set(map(lambda el: el.name, graph.getAllEdges())))

        # remove
        self.assertFalse(graph.removeNode(node2))
        self.assertTrue(graph.removeNode(node0))
        self.assertFalse(graph.hasNode(node0))
        self.assertFalse(graph.hasEdge(node0, node1))

    def testCongestionGraph(self):
        graph = CongestionGPSGraph(name='congestion_graph')

        node0 = Node(name='node0')
        node1 = Node(name='node1')
        node2 = Node(name='node2')

        func0 = lambda x: x * x + 2
        func1 = lambda x: x

        graph.addNode(node0)
        graph.addNode(node1)
        graph.addEdge(node0, node1)

        graph.setCongestionFunction(node0, node1, func0)
        graph.setCongestionFunction(node0, node2, func1)

        self.assertTrue(graph.hasCongestionFunction(node0, node1))
        self.assertFalse(graph.hasCongestionFunction(node0, node2))
        self.assertIsNotNone(graph.getCongestionFunction(node0, node1))
        self.assertIsNone(graph.getCongestionFunction(node1, node0))
        self.assertEqual({('node0', 'node1'): func0}, graph.getAllCongestionFunctions())

        self.assertTrue(graph.removeCongestionFunction(node0, node1))
        self.assertFalse(graph.removeCongestionFunction(node1, node0))
        self.assertFalse(graph.hasCongestionFunction(node0, node1))


if __name__ == '__main__':
    unittest.main()
