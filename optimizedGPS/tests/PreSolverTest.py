import unittest

from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS.problems.PreSolver import GlobalPreSolver, DrivingTimeIntervalPresolver, LowerUpperBoundsPresolver
from optimizedGPS.problems.simulator.Simulator import FromEdgeDescriptionSimulator
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

    def test_drivers_interval_presolver_feasibility(self):
        """
        Check if the shortest paths gives a feasible solution
        """
        graph = generate_grid_data(10, 10)
        for _ in range(5):
            drivers_graph = generate_random_drivers(graph)
            presolver = DrivingTimeIntervalPresolver(graph, drivers_graph)
            presolver.solve()

            solution = {}
            for driver in drivers_graph.get_all_drivers():
                solution[driver] = graph.get_shortest_path(
                    driver.start, driver.end, key=lambda u, v: graph.get_congestion_function(u, v)(0))

            simulator = FromEdgeDescriptionSimulator(graph, drivers_graph, solution)
            simulator.simulate()

            for driver in drivers_graph.get_all_drivers():
                starting_times = simulator.get_starting_times(driver)
                edges = list(graph.iter_edges_in_path(solution[driver]))
                i = 0
                while i < len(edges) - 1:
                    edge = edges[i]
                    start, end = presolver.drivers_structure.get_presence_interval(driver, edge)
                    s, e = starting_times[edge], starting_times[edges[i + 1]]
                    print "%s:%s: %s <= %s <= %s <= %s" % (driver, edge, start, s, e, end)
                    self.assertLessEqual(start, s)
                    self.assertGreaterEqual(end, e)
                    i += 1


    def test_lower_upper_bound_presolver(self):
        graph = generate_grid_data(10, 10)
        graph.set_global_congestion_function(lambda x: 3 * x + 4)

        drivers_graph = generate_random_drivers(graph, 10)

        presolver = LowerUpperBoundsPresolver(graph, drivers_graph)
        presolver.solve()

        for driver in drivers_graph.get_all_drivers():
            possible_edges = set(presolver.drivers_structure.get_possible_edges_for_driver(driver))
            for edge in graph.iter_edges_in_path(presolver.lower_bound.get_optimal_driver_path(driver)):
                self.assertIn(edge, possible_edges)
            for edge in graph.iter_edges_in_path(presolver.upper_bound.get_optimal_driver_path(driver)):
                self.assertIn(edge, possible_edges)



if __name__ == "__main__":
    unittest.main()
