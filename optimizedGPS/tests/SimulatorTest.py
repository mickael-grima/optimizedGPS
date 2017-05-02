# -*- coding: utf-8 -*-
# !/bin/env python

import unittest

import mock

from optimizedGPS.problems.simulator import FromEdgeDescriptionSimulator
from optimizedGPS.structure import GPSGraph, Driver, DriversGraph


class SimulatorTest(unittest.TestCase):

    @mock.patch.object(GPSGraph, 'get_congestion_function', lambda self, source, target: lambda x: x + 2)
    def test_simulator_from_edge_description(self):
        graph = GPSGraph(name='graph-test')
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)
        graph.add_edge(1, 2, traffic_limit=0)
        graph.add_edge(2, 3, traffic_limit=0)

        drivers_graph = DriversGraph()
        driver0 = Driver(1, 3, 0)
        driver1 = Driver(2, 3, 1)
        driver2 = Driver(2, 3, 1)
        driver3 = Driver(1, 3, 1)
        drivers_graph.add_driver(driver0)
        drivers_graph.add_driver(driver1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        edge_description = {
            driver0: (1, 2, 3),
            driver1: (2, 3),
            driver2: (2, 3),
            driver3: (1, 2, 3)
        }

        simulator = FromEdgeDescriptionSimulator(graph, drivers_graph, edge_description)
        simulator.simulate()

        self.assertEqual(simulator.get_traffic((2, 3), 2), 2)
        self.assertEqual(
            simulator.get_starting_times(driver0),
            {(1, 2): 0, (2, 3): 2, (3, simulator.EXIT): 6}
        )
        self.assertEqual(simulator.get_sum_driving_time(), 16)
        self.assertEqual(simulator.get_maximum_driving_time(), 7)
        self.assertEqual(simulator.get_edge_description(), edge_description)


if __name__ == '__main__':
    unittest.main()
