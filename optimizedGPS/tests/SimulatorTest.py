# -*- coding: utf-8 -*-
# !/bin/env python

import unittest
import random

from optimizedGPS.problems.simulator import FromEdgeDescriptionSimulator
from optimizedGPS.structure import GPSGraph, Driver, DriversGraph
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS import options


class SimulatorTest(unittest.TestCase):
    def test_simulator_from_edge_description(self):
        graph = GPSGraph(name='graph-test')
        graph.add_node(1)
        graph.add_node(2)
        graph.add_node(3)
        graph.add_edge(1, 2, traffic_limit=0)
        graph.add_edge(2, 3, traffic_limit=0)
        graph.set_global_congestion_function(lambda x: x + 2)

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
            {(1, 2): 0, (2, 3): 2, (3, options.EXIT): 6}
        )
        self.assertEqual(simulator.get_sum_driving_time(), 16)
        self.assertEqual(simulator.get_maximum_driving_time(), 7)
        self.assertEqual(simulator.get_edge_description(), edge_description)

    def test_shortest_path(self):
        """
        Test if the shortest paths always give the best solution
        """
        grid_graph = generate_grid_data(10, 10)
        grid_graph.set_global_congestion_function(lambda x: 3 * x + 4)
        for _ in range(10):
            drivers_graph = generate_random_drivers(grid_graph, 10)
            edge_description = {
                driver: grid_graph.get_shortest_path(driver.start, driver.end, key=grid_graph.get_minimum_waiting_time)
                for driver in drivers_graph.get_all_drivers()
            }
            simulator = FromEdgeDescriptionSimulator(grid_graph, drivers_graph, edge_description)
            simulator.simulate()

            def get_path_length(path):
                return sum(grid_graph.get_minimum_waiting_time(*e) for e in grid_graph.iter_edges_in_path(path))

            self.assertLessEqual(
                sum(map(get_path_length, edge_description.itervalues())),
                simulator.get_value()
            )

    def test_partial_solution(self):
        """
        Test whether removing a driver gives a better solution
        """
        grid_graph = generate_grid_data(10, 10)
        grid_graph.set_global_congestion_function(lambda x: 3 * x + 4)
        for _ in range(10):
            drivers_graph = generate_random_drivers(grid_graph, 10)
            edge_description = {
                driver: grid_graph.get_shortest_path(driver.start, driver.end, key=grid_graph.get_minimum_waiting_time)
                for driver in drivers_graph.get_all_drivers()
            }
            simulator = FromEdgeDescriptionSimulator(grid_graph, drivers_graph, edge_description)
            simulator.simulate()
            opt_value = simulator.get_value()

            # Choose a random driver
            driver = list(drivers_graph.get_all_drivers())[random.randint(0, 9)]
            driver_path = edge_description[driver]
            del edge_description[driver]

            simulator = FromEdgeDescriptionSimulator(grid_graph, drivers_graph, edge_description)
            simulator.simulate()
            partial_value = simulator.get_value()

            def get_path_length(path):
                return sum(grid_graph.get_minimum_waiting_time(*e) for e in grid_graph.iter_edges_in_path(path))

            self.assertLessEqual(
                partial_value + driver.time + get_path_length(driver_path),
                opt_value
            )


if __name__ == '__main__':
    unittest.main()
