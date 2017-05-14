import unittest

from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS.problems.PreSolver import GlobalPreSolver, DrivingTimeIntervalPresolver
from optimizedGPS.structure.Driver import Driver
from optimizedGPS.structure.DriversGraph import DriversGraph
from optimizedGPS.structure.GPSGraph import GPSGraph


class PreSolverTest(unittest.TestCase):
    def test_get_driver_useless_edges_for_global_presolver(self):
        """
        For a test graph we test the function which provides the edges on which every drivers will never drive
        """
        grid_graph = generate_grid_data(length=3, width=3)
        drivers_graph = DriversGraph()
        grid_graph.add_edge("n_1_1", "n_0_1")
        grid_graph.set_global_congestion_function(lambda x: x + 1)
        driver = Driver("n_1_0", "n_2_2", 2)
        drivers_graph.add_driver(driver)

        presolver = GlobalPreSolver(grid_graph, drivers_graph)

        # Some edges are reachable for driver, but he won't driver on it
        driver_reachable_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_2_1", "n_2_2"), driver_reachable_edges)
        self.assertNotIn(("n_0_1", "n_0_2"), driver_reachable_edges)

        # If the traffic is dense, the previous edge will be reachable
        for _ in range(10):
            drivers_graph.add_driver(Driver("n_0_0", "n_2_2", 0))
        presolver = GlobalPreSolver(grid_graph, drivers_graph)
        driver_reachable_edges = set(presolver.iter_reachable_edges_for_driver(driver))
        self.assertIn(("n_0_1", "n_0_2"), driver_reachable_edges)

        # Test if shortest path belong to reachable edges
        grid_graph = generate_grid_data(10, 10)
        grid_graph.set_global_congestion_function(lambda x: 3 * x + 4)
        for _ in range(4):
            drivers_graph = generate_random_drivers(grid_graph)
            presolver = GlobalPreSolver(grid_graph, drivers_graph)
            for driver in drivers_graph.get_all_drivers():
                driver_reachable_edges = set(presolver.iter_reachable_edges_for_driver(driver))
                edges = grid_graph.iter_edges_in_path(
                    grid_graph.get_shortest_path(driver.start, driver.end, key=grid_graph.get_minimum_waiting_time)
                )
                for edge in edges:
                    self.assertIn(
                        edge, driver_reachable_edges,
                        msg="Driver: %s\nEdge: %s\nReachable edges: %s"
                            % (driver.to_tuple(), edge, driver_reachable_edges)
                    )

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
