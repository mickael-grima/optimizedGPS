# -*- coding: utf-8 -*-
# !/bin/env python

import unittest
from collections import defaultdict

from optimizedGPS import labels
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers
from optimizedGPS.problems.Heuristics import RealGPS
from optimizedGPS.problems.Models import TEGModel
from optimizedGPS.structure import Driver, DriversGraph, GPSGraph


class ProblemsTest(unittest.TestCase):
    def testTEGModel(self):
        # 1 driver
        graph = GPSGraph()
        graph.add_edge("0", "1", **{labels.CONGESTION_FUNC: lambda x: x + 2})
        graph.add_edge("0", "2", **{labels.CONGESTION_FUNC: lambda x: 2 * x + 2})
        graph.add_edge("1", "2", **{labels.CONGESTION_FUNC: lambda x: x + 1})

        drivers_graph = DriversGraph()
        driver = Driver("0", "2", 0)
        drivers_graph.add_driver(driver)

        model = TEGModel(graph, drivers_graph, horizon=2)
        model.build_model()

        self.assertEqual(len(model.x), 9)  # number of variables

        model.solve()

        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.value, 2)

        # 3 drivers
        driver2 = Driver("0", "2", 0)
        driver3 = Driver("0", "2", 1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        model = TEGModel(graph, drivers_graph, horizon=4)
        model.build_model()

        self.assertEqual(len(model.x), 90)

        model.solve()

        # test big M: is big M greater than the greatest waiting time ?
        for i in range(4):
            max_traffic = max(
                graph.get_congestion_function(*edge)(
                    sum(
                        sum(
                            model.x[model.TEGgraph.build_edge(edge, i, j), d].X
                            for j in model.drivers_structure.iter_ending_times(driver, edge, starting_time=i)
                            if (model.TEGgraph.build_edge(edge, i, j), d) in model.x
                        )
                        for d in drivers_graph.get_all_drivers()
                    )
                )
                for edge in graph.edges_iter())
            self.assertGreaterEqual(model.bigM(), max_traffic)

        # Check feasibility
        x = defaultdict(lambda: 0)
        x[model.TEGgraph.build_edge(("0", "1"), 1, 3), driver3] = 1
        x[model.TEGgraph.build_edge(("1", "2"), 3, 4), driver3] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver2] = 1
        self.assertTrue(model.check_feasibility(x))
        self.assertEqual(model.get_objective_from_solution(x), 8)

        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 0, 2), driver2] = 1
        x[model.TEGgraph.build_edge(("0", "2"), 1, 7), driver3] = 1
        self.assertTrue(model.check_feasibility(x))
        self.assertEqual(model.get_objective_from_solution(x), 11)

        x = defaultdict(lambda: 0)
        for key, var in model.x.iteritems():
            x[key] = var.X
        self.assertTrue(model.check_feasibility(x))

        # Check optimality
        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.opt_solution[driver2], ('0', '2'))
        self.assertEqual(model.opt_solution[driver3], ('0', '1', '2'))
        self.assertEqual(model.value, 8)

    def test_real_GPS(self):
        graph = GPSGraph()
        graph.add_edge(0, 1, congestion_func=lambda x: 3 * x + 3)
        graph.add_edge(0, 2, congestion_func=lambda x: 4)
        graph.add_edge(1, 3, congestion_func=lambda x: 1)
        graph.add_edge(2, 3, congestion_func=lambda x: 4)
        graph.add_edge(3, 1, congestion_func=lambda x: 13)

        driver1 = Driver(0, 3, 0)
        driver2 = Driver(0, 3, 1)
        driver3 = Driver(0, 1, 2)
        drivers_graph = DriversGraph()
        drivers_graph.add_driver(driver1)
        drivers_graph.add_driver(driver2)
        drivers_graph.add_driver(driver3)

        heuristic = RealGPS(graph, drivers_graph)
        heuristic.solve()

        self.assertEqual(heuristic.get_optimal_driver_path(driver1), (0, 1, 3))
        self.assertEqual(heuristic.get_optimal_driver_path(driver2), (0, 1, 3))
        self.assertEqual(heuristic.get_optimal_driver_path(driver3), (0, 1))
        self.assertEqual(heuristic.get_optimal_value(), 23)

    def test_opt_solution_for_real_GPS(self):
        graph = generate_grid_data(10, 10)
        graph.set_global_congestion_function(lambda x: 3 * x + 4)
        for _ in xrange(10):
            drivers_graph = generate_random_drivers(graph, 10)
            heuristic = RealGPS(graph, drivers_graph)
            heuristic.solve()
            for driver, path in heuristic.opt_solution.iteritems():
                self.assertEqual(path[0], driver.start)
                self.assertEqual(path[-1], driver.end)


if __name__ == '__main__':
    unittest.main()
