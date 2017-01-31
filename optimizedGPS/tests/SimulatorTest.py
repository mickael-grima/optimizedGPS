# -*- coding: utf-8 -*-
# !/bin/env python

from optimizedGPS.logger import configure

configure()

import unittest
from optimizedGPS.problems.simulator import GPSSimulator
from optimizedGPS.problems.simulator import FiniteHorizonSimulator
from optimizedGPS.problems.simulator import ModelTransformationSimulator
from optimizedGPS.problems.simulator.utils import get_id
from optimizedGPS.data.data_generator import generate_graph_from_file
from optimizedGPS.structure import GPSGraph


class SimulatorTest(unittest.TestCase):

    def testStructure(self):
        graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml',
                                         traffic_limit=0)
        # add drivers
        graph.add_driver('1', '6', 0, nb=2)
        graph.add_driver('3', '6', 1, nb=3)
        graph.add_driver('3', '4', 1, nb=1)
        graph.add_driver('5', '6', 2, nb=2)
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
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)
        graph.add_edge(1, 2, traffic_limit=0)
        graph.add_edge(2, 3, traffic_limit=0)

        graph.add_driver(1, 3, starting_time=0)
        graph.add_driver(2, 3, starting_time=1, nb=2)
        graph.add_driver(1, 3, starting_time=1)

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
        self.assertEqual(0, simulator.time)

        simulator.next()
        # 1st step
        self.assertEqual([{-1: [1, 1], 0: []}, {-1: [1], 0: [1], 1: []}], simulator.clocks)
        self.assertEqual(1, simulator.time)

        simulator.next()
        # 2nd step
        self.assertEqual([{-1: [], 0: [1, 2]}, {-1: [], 0: [1], 1: [17]}], simulator.clocks)
        self.assertEqual(22, simulator.time)

        simulator.next()
        # 3rd step
        self.assertEqual([{-1: [], 0: [1]}, {-1: [], 0: [], 1: [16, 17]}], simulator.clocks)
        self.assertEqual(39, simulator.time)

        simulator.next()
        # 4th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: [15, 16]}], simulator.clocks)
        self.assertEqual(39, simulator.time)

        simulator.next()
        # 5th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: [1]}], simulator.clocks)
        self.assertEqual(39, simulator.time)

        simulator.next()
        # 5th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: []}], simulator.clocks)
        self.assertEqual(39, simulator.time)

        # end
        self.assertFalse(simulator.has_next())

    def testModelTransformationSimulator(self):
        graph = GPSGraph(name='graph-test')
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)
        graph.add_edge(1, 2, traffic_limit=0)
        graph.add_edge(2, 3, traffic_limit=0)

        graph.add_driver(1, 3, starting_time=0)
        graph.add_driver(2, 3, starting_time=1, nb=2)
        graph.add_driver(1, 3, starting_time=1)

        paths = {
            (1, 2, 3): {
                0: 1,
                1: 1
            },
            (2, 3): {
                1: 2
            }
        }

        simulator = ModelTransformationSimulator(graph, paths)

        # initialization
        self.assertEqual([{-1: [1, 1], 0: []}, {-1: [0, 1], 0: [], 1: []}], simulator.clocks)
        self.assertEqual(0, simulator.time)

        simulator.next()
        # 1st step
        self.assertEqual([{-1: [1, 1], 0: []}, {-1: [1], 0: [1], 1: []}], simulator.clocks)
        self.assertEqual(1, simulator.time)

        simulator.next()
        # 2nd step
        self.assertEqual([{-1: [], 0: [1, 1]}, {-1: [], 0: [2], 1: [1]}], simulator.clocks)
        self.assertEqual(6, simulator.time)

        simulator.next()
        # 3rd step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [1], 1: []}], simulator.clocks)
        self.assertEqual(6, simulator.time)

        simulator.next()
        # 4th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: [1]}], simulator.clocks)
        self.assertEqual(7, simulator.time)

        simulator.next()
        # 5th step
        self.assertEqual([{-1: [], 0: []}, {-1: [], 0: [], 1: []}], simulator.clocks)
        self.assertEqual(7, simulator.time)

    def testFiniteHorizonSimulator(self):
        graph = generate_graph_from_file('static/graph-test-1.graphml')

        graph.add_driver('1', '4', starting_time=0)
        graph.add_driver('1', '4', starting_time=1, nb=2)
        graph.add_driver('2', '4', starting_time=1)

        simulator = FiniteHorizonSimulator(graph)

        # Initialization
        state = "Drivers ('1', '4', 0) are on path ('1',) and move in 0.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1',) and move in 1.0, 1.0 time's unit(s). 2 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path ('2',) and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        self.assertEqual(state, simulator.print_state())

        # 1st step
        nxt_edges = {
            get_id((('1', '4', 0), ('1',))): {('1', '2'): 1},
            get_id((('1', '4', 1), ('1',))): {('1', '3'): 1, ('1', '2'): 1},
            get_id((('2', '4', 1), ('2',))): {('2', '4'): 1}
        }
        simulator.updateNextEdges(nxt_edges)
        state = "Drivers ('1', '4', 0) are on path ('1',) and move in 0.0 time's unit(s). 1 will move on edge ('1', '2').\n"
        state += "Drivers ('1', '4', 1) are on path ('1',) and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path ('2',) and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 0) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1',) and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path ('2',) and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        # 2nd step
        nxt_edge = {get_id((('1', '4', 0), ('1', '2'))): {('2', '4'): 1}}
        simulator.updateNextEdges(nxt_edge)
        state = "Drivers ('1', '4', 0) are on path ('1', '2') and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        state += "Drivers ('1', '4', 1) are on path ('1',) and move in 1.0, 1.0 time's unit(s). 1 will move on edge ('1', '2'), 1 will move on edge ('1', '3').\n"
        state += "Drivers ('2', '4', 1) are on path ('2',) and move in 1.0 time's unit(s). 1 will move on edge ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 0) are on path ('1', '2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 2.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())

        saved_state = simulator.get_current_state()

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
        state += "1 drivers ('1', '4', 0) are arrived. They've driven on path ('1', '2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        # 4th step
        nxt_edge = {}
        simulator.updateNextEdges(nxt_edge)
        state = "Drivers ('1', '4', 1) are on path ('1', '2', '4') and move in 17.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "1 drivers ('1', '4', 0) are arrived. They've driven on path ('1', '2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        simulator.next()
        state = "Drivers ('1', '4', 1) are on path ('1', '2', '4') and move in 16.0 time's unit(s). They have reached the ending node.\n"
        state += "1 drivers ('1', '4', 0) are arrived. They've driven on path ('1', '2', '4').\n"
        state += "1 drivers ('1', '4', 1) are arrived. They've driven on path ('1', '3', '4').\n"
        state += "1 drivers ('2', '4', 1) are arrived. They've driven on path ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        # 5th step
        simulator.next()
        state = "1 drivers ('1', '4', 0) are arrived. They've driven on path ('1', '2', '4').\n"
        state += "1 drivers ('1', '4', 1) are arrived. They've driven on path ('1', '2', '4').\n"
        state += "1 drivers ('1', '4', 1) are arrived. They've driven on path ('1', '3', '4').\n"
        state += "1 drivers ('2', '4', 1) are arrived. They've driven on path ('2', '4').\n"
        self.assertEqual(state, simulator.print_state())

        # Final
        self.assertFalse(simulator.has_next())
        self.assertEqual(simulator.get_value(), 24)

        # saved state
        simulator.reinitialize(state=saved_state)
        state = "Drivers ('1', '4', 0) are on path ('1', '2', '4') and move in 1.0 time's unit(s). They have reached the ending node.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '2') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('1', '4', 1) are on path ('1', '3') and move in 1.0 time's unit(s). 1 of them are waiting for next edges.\n"
        state += "Drivers ('2', '4', 1) are on path ('2', '4') and move in 2.0 time's unit(s). They have reached the ending node.\n"
        self.assertEqual(state, simulator.print_state())


if __name__ == '__main__':
    unittest.main()
