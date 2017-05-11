import unittest

import mock

from optimizedGPS.data.data_generator import generate_grid_data
from optimizedGPS.problems.PreSolver import DriverPreSolver, GlobalPreSolver
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


if __name__ == "__main__":
    unittest.main()
