# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

from logger import configure

configure()

import unittest
from simulator.GPSSimulator import GPSSimulator
from data_generator import generate_graph_from_file
from structure.GPSGraph import GPSGraph


class SimulatorTest(unittest.TestCase):

    def testStructure(self):
        graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml')
        # add drivers
        graph.addDriver('n0', 'n5', 0, nb=2)
        graph.addDriver('n2', 'n5', 1, nb=3)
        graph.addDriver('n2', 'n3', 1, nb=1)
        graph.addDriver('n4', 'n5', 2, nb=2)
        # get path for drivers
        paths = {
            ('n0', 'n2', 'n3', 'n5'): {0: 2},
            ('n2', 'n3', 'n5'): {1: 2},
            ('n2', 'n4', 'n5'): {1: 1},
            ('n2', 'n3'): {1: 1},
            ('n4', 'n5'): {2: 2}
        }
        simulator = GPSSimulator(graph, paths)

        # structure
        self.assertEqual(simulator.graph, graph)
        self.assertEqual(set(simulator.paths), set(paths.iterkeys()))

    def testSimulation(self):
        graph = GPSGraph(name='graph-test')
        graph.addNode(1)
        graph.addNode(2)
        graph.addNode(3)
        graph.addEdge(1, 2)
        graph.addEdge(2, 3)

        graph.addDriver(1, 3, starting_time=0)
        graph.addDriver(2, 3, starting_time=1, nb=2)
        graph.addDriver(1, 3, starting_time=1)

        paths = {
            (1, 2, 3): {
                0: 1,
                1: 1
            },
            (2, 3): {
                1: 2
            }
        }

        simulator = GPSSimulator(graph, paths)

        # initialization
        self.assertEqual([{-1: [1, 1], 0: []}, {-1: [0, 1], 0: [], 1: []}], simulator.clocks)
        self.assertEqual({(1, 2): 0, (2, 3): 0}, simulator.times)

        simulator.next()
        # 1st step
        self.assertEqual([{-1: [1, 1], 0: []}, {-1: [1], 0: [1], 1: []}], simulator.clocks)
        self.assertEqual({(1, 2): 1, (2, 3): 0}, simulator.times)

        simulator.next()
        # 2nd step
        self.assertEqual([{-1: [], 0: [1, 2]}, {-1: [], 0: [2], 1: [17]}], simulator.clocks)
        self.assertEqual({(1, 2): 3, (2, 3): 20}, simulator.times)

        simulator.next()
        # 3rd step
        self.assertEqual([{-1: [], 0: [1]}, {-1: [], 0: [1], 1: [16]}], simulator.clocks)
        self.assertEqual({(1, 2): 3, (2, 3): 20}, simulator.times)

        simulator.next()
        # 4th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: [15, 82]}], simulator.clocks)
        self.assertEqual({(1, 2): 3, (2, 3): 102}, simulator.times)

        simulator.next()
        # 5th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: [67]}], simulator.clocks)
        self.assertEqual({(1, 2): 3, (2, 3): 102}, simulator.times)

        simulator.next()
        # 5th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: []}], simulator.clocks)
        self.assertEqual({(1, 2): 3, (2, 3): 102}, simulator.times)

        # end
        self.assertFalse(simulator.has_next())


if __name__ == '__main__':
    unittest.main()
