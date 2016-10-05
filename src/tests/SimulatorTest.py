# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

from logger import configure

configure()

import unittest
from simulator.GPSSimulator import GPSSimulator
from simulator.FiniteHorizonSimulator import FiniteHorizonSimulator
from simulator.utils.tools import get_id
from data_generator import generate_graph_from_file
from structure.GPSGraph import GPSGraph


class SimulatorTest(unittest.TestCase):

    def testStructure(self):
        graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml')
        # add drivers
        graph.addDriver('1', '6', 0, nb=2)
        graph.addDriver('3', '6', 1, nb=3)
        graph.addDriver('3', '4', 1, nb=1)
        graph.addDriver('5', '6', 2, nb=2)
        # get path for drivers
        paths = {
            ('1', '3', '4', '6'): {0: 2},
            ('3', '4', '6'): {1: 2},
            ('3', '5', '6'): {1: 1},
            ('3', '4'): {1: 1},
            ('5', '6'): {2: 2}
        }
        simulator = GPSSimulator(graph, paths)

        # structure
        self.assertEqual(simulator.graph, graph)
        self.assertEqual(set(simulator.paths), set(paths.iterkeys()))

    def testGPSSimulator(self):
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

    def testFiniteHorizonSimulator(self):
        graph = generate_graph_from_file('static/graph-test-1.graphml')

        graph.addDriver('1', '4', starting_time=0)
        graph.addDriver('1', '4', starting_time=1, nb=2)
        graph.addDriver('2', '4', starting_time=1)

        simulator = FiniteHorizonSimulator(graph)

        # Initialization
        state = "Drivers ('1', '4', 0) are on path () and move in 0.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path () and move in 1.0, 1.0 time's unit(s). 2 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path () and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        self.assertEqual(state, simulator.print_state())

        # 1st step
        nxt_edges = {
            get_id((('1', '4', 0), ())): {('1', '2'): 1},
            get_id((('1', '4', 1), ())): {('1', '3'): 1, ('1', '2'): 1},
            get_id((('2', '4', 1), ())): {('2', '4'): 1}
        }
        simulator.updateNextEdges(nxt_edges)
        state = "Drivers ('1', '4', 0) are on path () and move in 0.0 time's unit(s). 1 will move on edge ('1', '2').\n"
        state += "Drivers ('1', '4', 1) are on path () and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path () and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 0) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path () and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path () and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        # 2nd step
        nxt_edge = {get_id((('1', '4', 0), ('1', '2'))): {('2', '4'): 1}}
        simulator.updateNextEdges(nxt_edge)
        state = "Drivers ('1', '4', 0) are on path ('1', '2') and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        state += "Drivers ('1', '4', 1) are on path () and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path () and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 0) are on path ('1', '2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 2.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        saved_state = simulator.getCurrentState()

        # 3rd step
        nxt_edge = {get_id((('1', '4', 1), ('1', '3'))): {('3', '4'): 1},
                    get_id((('1', '4', 1), ('1', '2'))): {('2', '4'): 1}}
        simulator.updateNextEdges(nxt_edge)
        state = "Drivers ('1', '4', 0) are on path ('1', '2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '2') and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3') and move in 1.0 time's unit(s). 1 will move on edge ('3', '4').\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 2.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 1) are on path ('1', '2', '4') and move in 17.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        # 4th step
        nxt_edge = {}
        simulator.updateNextEdges(nxt_edge)
        state = "Drivers ('1', '4', 1) are on path ('1', '2', '4') and move in 17.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 1) are on path ('1', '2', '4') and move in 16.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        # 5th step
        simulator.next()
        state = ''
        self.assertEqual(state, simulator.print_state())

        # Final
        self.assertFalse(simulator.has_next())
        self.assertEqual(simulator.get_total_time(), 24)

        # saved state
        simulator.reinitialize(state=saved_state)
        state = "Drivers ('1', '4', 0) are on path ('1', '2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 2.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())


if __name__ == '__main__':
    unittest.main()
