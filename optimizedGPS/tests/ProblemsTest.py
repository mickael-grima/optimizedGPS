# -*- coding: utf-8 -*-
# !/bin/env python

import unittest

from optimizedGPS import labels
from optimizedGPS.problems.Heuristics import RealGPS
from optimizedGPS.problems.Models import TEGModel
from optimizedGPS.structure import Driver, DriversGraph, GPSGraph
from optimizedGPS.data.data_generator import generate_grid_data, generate_random_drivers


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

        # self.assertEqual(filter(lambda v: v.X == 1, model.x.itervalues()), 2)
        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.opt_solution[driver2], ('0', '2'))
        self.assertEqual(model.opt_solution[driver3], ('0', '1', '2'))
        self.assertEqual(model.value, 8)

    def test_TEG_model_on_congestioned_graph(self):
        graph = GPSGraph()
        graph.add_node("source1")
        graph.add_node("source2")
        graph.add_node("middle")
        graph.add_node("target")
        graph.add_edge("source1", "middle", congestion_func=lambda x: x + 3)
        graph.add_edge("source2", "middle", congestion_func=lambda x: x + 3)
        graph.add_edge("source1", "target", congestion_func=lambda x: 5 * x + 7)
        graph.add_edge("source2", "target", congestion_func=lambda x: 5 * x + 7)
        graph.add_edge("middle", "target", congestion_func=lambda x: 2 * x + 3)

        drivers_graph = DriversGraph()
        for i in xrange(10):
            drivers_graph.add_driver(Driver("source1", "target", i))
        for i in xrange(10):
            drivers_graph.add_driver(Driver("source2", "target", i))

        model = TEGModel(graph, drivers_graph, horizon=57)
        model.build_model()
        model.solve()

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
