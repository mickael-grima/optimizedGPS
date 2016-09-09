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
from data.data_generator import DataGenerator


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
        graph.addEdge(node0, node1, size=3)

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

        # attribute
        edge = graph.getAllEdges().pop()
        self.assertEqual(edge.size, 3)

        # remove
        self.assertFalse(graph.removeNode(node2))
        self.assertTrue(graph.removeNode(node0))
        self.assertFalse(graph.hasNode(node0))
        self.assertFalse(graph.hasEdge(node0, node1))

    def testBuildGraph(self):
        data = DataGenerator.generate_grid_data(length=2, width=3, size=3)
        graph = GPSGraph.buildGraph(data)

        self.assertEqual(set(['node_%s_%s' % (i, j) for i in range(2) for j in range(3)]),
                         set(map(lambda el: el.name, graph.getAllNodes())))
        self.assertIn('node_0_1 --> node_1_1', map(lambda el: el.name, graph.getAllEdges()))

    def testCongestionGraph(self):
        data = DataGenerator.generate_grid_data(length=2, width=3, size=3)
        graph = CongestionGPSGraph.buildGraph(data)

        congFunctions = graph.getAllCongestionFunctions()
        self.assertTrue(congFunctions)


if __name__ == '__main__':
    unittest.main()
