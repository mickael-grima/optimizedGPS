import unittest

import mock

from optimizedGPS.data.data_generator import generate_grid_data
from optimizedGPS.problems.PreSolver import DriverPreSolver, GlobalPreSolver, DrivingTimeIntervalPresolver
from optimizedGPS.structure.Driver import Driver
from optimizedGPS.structure.GPSGraph import GPSGraph
from optimizedGPS.structure.DriversGraph import DriversGraph


class PreSolverTest(unittest.TestCase):
    @mock.patch.object(GPSGraph, 'get_congestion_function', lambda self, source, target: lambda x: x + 1)
    def test_get_driver_useless_edges_for_driver_presolver(self):
        """
        For a test graph we test the function which provides the edges on which every drivers will never drive
        """
        grid_graph = generate_grid_data(length=3, width=3)
        drivers_graph = DriversGraph()
        grid_graph.add_edge("n_1_1", "n_0_1")
        driver = Driver("n_1_0", "n_2_2", 2)
        drivers_graph.add_driver(driver)

        presolver = DriverPreSolver(grid_graph, drivers_graph)

        # Some edges are reachable for driver, but he won't driver on it
        driver_unused_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_2_1", "n_2_2"), driver_unused_edges)
        self.assertNotIn(("n_0_1", "n_0_2"), driver_unused_edges)

        # If the traffic is dense, the previous edge will be reachable
        for _ in range(10):
            drivers_graph.add_driver(Driver("n_0_0", "n_2_2", 0))
        presolver = DriverPreSolver(grid_graph, drivers_graph)
        driver_unused_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_0_1", "n_0_2"), driver_unused_edges)

    @mock.patch.object(GPSGraph, 'get_congestion_function', lambda self, source, target: lambda x: x + 1)
    def test_get_driver_useless_edges_for_global_presolver(self):
        """
        For a test graph we test the function which provides the edges on which every drivers will never drive
        """
        grid_graph = generate_grid_data(length=3, width=3)
        drivers_graph = DriversGraph()
        grid_graph.add_edge("n_1_1", "n_0_1")
        driver = Driver("n_1_0", "n_2_2", 2)
        drivers_graph.add_driver(driver)

        presolver = GlobalPreSolver(grid_graph, drivers_graph)

        # Some edges are reachable for driver, but he won't driver on it
        driver_unused_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_2_1", "n_2_2"), driver_unused_edges)
        self.assertNotIn(("n_0_1", "n_0_2"), driver_unused_edges)

        # If the traffic is dense, the previous edge will be reachable
        for _ in range(10):
            drivers_graph.add_driver(Driver("n_0_0", "n_2_2", 0))
        presolver = GlobalPreSolver(grid_graph, drivers_graph)
        driver_unused_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_0_1", "n_0_2"), driver_unused_edges)

    def test_drivers_interval_presolver(self):
        graph = GPSGraph()
        graph.add_edge(1, 2, congestion_func=lambda x: x + 1)
        graph.add_edge(1, 3, congestion_func=lambda x: 2 * x + 2)
        graph.add_edge(2, 3, congestion_func=lambda x: x + 1)

        drivers_graph = DriversGraph()
        driver1 = Driver(1, 3, 0)
        driver2 = Driver(1, 3, 1)
        driver3 = Driver(1, 3, 2)
        drivers_graph.add_driver(driver1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        presolver = DrivingTimeIntervalPresolver(graph, drivers_graph, horizon=100)

        # initial state
        self.assertEqual(presolver.max_traffics[1, 3][driver1], 2)
        self.assertEqual(presolver.min_traffics[2, 3][driver3], 0)

        # 1st step
        presolver.next()
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver1, (1, 3)), (0, 6))
        self.assertEqual(presolver.drivers_structure.get_presence_interval(driver1, (2, 3)), (3, 2))
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver3, (1, 3)), (2, 8))
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver2, (2, 3)), (2, 7))
        self.assertEqual(presolver.get_minimum_traffic(driver1, (1, 3)), 0)
        self.assertEqual(presolver.get_minimum_traffic(driver3, (1, 3)), 2)
        self.assertEqual(presolver.get_maximum_traffic(driver1, (1, 3)), 0)
        self.assertEqual(presolver.get_maximum_traffic(driver3, (1, 3)), 2)
        self.assertEqual(presolver.get_minimum_traffic(driver1, (2, 3)), 0)
        self.assertEqual(presolver.get_minimum_traffic(driver3, (2, 3)), 1)
        self.assertEqual(presolver.get_maximum_traffic(driver1, (2, 3)), 1)
        self.assertEqual(presolver.get_maximum_traffic(driver3, (2, 3)), 2)

        # final
        presolver.solve()
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver1, (1, 3)), (0, 6))
        self.assertEqual(presolver.drivers_structure.get_presence_interval(driver1, (2, 3)), (1, 2))
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver3, (1, 3)), (2, 8))
        self.assertEqual(presolver.drivers_structure.get_safety_interval(driver2, (2, 3)), (3, 6))
        self.assertEqual(presolver.get_minimum_traffic(driver1, (1, 3)), 0)
        self.assertEqual(presolver.get_minimum_traffic(driver3, (1, 3)), 2)
        self.assertEqual(presolver.get_maximum_traffic(driver1, (1, 3)), 0)
        self.assertEqual(presolver.get_maximum_traffic(driver3, (1, 3)), 2)
        self.assertEqual(presolver.get_minimum_traffic(driver1, (2, 3)), 0)
        self.assertEqual(presolver.get_minimum_traffic(driver3, (2, 3)), 1)
        self.assertEqual(presolver.get_maximum_traffic(driver1, (2, 3)), 0)
        self.assertEqual(presolver.get_maximum_traffic(driver3, (2, 3)), 1)


if __name__ == "__main__":
    unittest.main()
