# -*- coding: utf-8 -*-
# !/bin/env python

import unittest

from optimizedGPS import options, labels
from optimizedGPS.data.data_generator import (
    generate_graph_from_file,
    generate_grid_data,
    generate_random_drivers
)
from optimizedGPS.problems.Comparator import BoundsHandler, MultipleGraphComparator, ResultsHandler
from optimizedGPS.problems.Heuristics import ShortestPathHeuristic, ShortestPathTrafficFree, RealGPS
from optimizedGPS.problems.Models import BestPathTrafficModel, FixedWaitingTimeModel, TEGModel
from optimizedGPS.structure import Driver, DriversGraph, GPSGraph


class ProblemsTest(unittest.TestCase):
    def setUp(self):
        self.graph0 = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)
        self.drivers_graph0 = DriversGraph()
        self.drivers_graph0.add_driver(Driver('1', '6', 0))
        self.drivers_graph0.add_driver(Driver('1', '6', 1))
        self.drivers_graph0.add_driver(Driver('1', '6', 1))
        self.drivers_graph0.add_driver(Driver('2', '6', 0))
        self.drivers_graph0.add_driver(Driver('2', '6', 2))
        self.drivers_graph0.add_driver(Driver('3', '6', 0))
        self.drivers_graph0.add_driver(Driver('3', '6', 1))
        self.drivers_graph0.add_driver(Driver('3', '6', 2))

        self.graph1 = generate_grid_data(length=3, width=5, graph_name='grid-graph-3-5-test')
        self.drivers_graph1 = DriversGraph()
        self.drivers_graph1.add_driver(Driver('n_0_0', 'n_2_4', 0))
        self.drivers_graph1.add_driver(Driver('n_0_0', 'n_2_4', 1))
        self.drivers_graph1.add_driver(Driver('n_0_0', 'n_2_4', 1))
        self.drivers_graph1.add_driver(Driver('n_0_1', 'n_2_4', 0))
        self.drivers_graph1.add_driver(Driver('n_0_1', 'n_2_4', 2))
        self.drivers_graph1.add_driver(Driver('n_1_0', 'n_2_4', 0))
        self.drivers_graph1.add_driver(Driver('n_1_0', 'n_2_4', 1))
        self.drivers_graph1.add_driver(Driver('n_1_0', 'n_2_4', 2))

    def testMultipleGraphComparator(self):
        comparator = MultipleGraphComparator()
        comparator.append_graphs((self.graph0, self.drivers_graph0), (self.graph1, self.drivers_graph1))
        comparator.append_algorithm(ShortestPathHeuristic, timeout=2)
        comparator.append_algorithm(BestPathTrafficModel, timeout=2)
        comparator.append_algorithm(ShortestPathTrafficFree, timeout=2)

        results = comparator.compare()
        self.assertEqual(len(results), len(comparator.graphs))
        for i in range(len(results)):
            graph, res = comparator.graphs[i], results[i]
            for algo, rs in res.iteritems():
                self.assertIn(rs[2], ['SUCCESS', 'TIMEOUT'], 'FAILED for algo %s on graph %s' % (algo, graph))

    def testBoundHandler(self):
        graph = generate_grid_data()
        drivers_graph = generate_random_drivers(graph)
        handler = BoundsHandler()
        handler.set_graphs(graph, drivers_graph)

        # add bounds
        handler.append_lower_bound(ShortestPathTrafficFree)
        handler.append_upper_bound(ShortestPathHeuristic)

        # bompute bounds
        handler.compute_bounds()

        self.assertGreaterEqual(handler.get_upper_bound(), handler.get_lower_bound())

    def testResultsHandler(self):
        handler = ResultsHandler()
        handler.append_graphs((self.graph0, self.drivers_graph0), (self.graph1, self.drivers_graph1))

        handler.append_lower_bound(ShortestPathTrafficFree)
        handler.append_upper_bound(ShortestPathHeuristic)

        handler.append_algorithm(BestPathTrafficModel, timeout=2)
        handler.append_algorithm(FixedWaitingTimeModel, timeout=2)
        handler.append_algorithm(RealGPS, timeout=2)
        # handler.append_algorithm(TEGLinearCongestionModel, timeout=2)

        results = handler.compare()

        for i in range(len(results)):
            graph, res = handler.graphs[i].graph, results[i]
            self.assertGreaterEqual(res[options.LOWER_BOUND_LABEL], 0)
            self.assertGreaterEqual(res[options.UPPER_BOUND_LABEL], res[options.LOWER_BOUND_LABEL])
            for algo, rs in res.iteritems():
                if algo not in [options.LOWER_BOUND_LABEL, options.UPPER_BOUND_LABEL]:
                    self.assertIn(rs[2], ['SUCCESS', 'TIMEOUT'], 'FAILED for algo %s on graph %s' % (algo, graph))

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

        self.assertEqual(len(model.x), 90)

        model.solve()

        # self.assertEqual(filter(lambda v: v.X == 1, model.x.itervalues()), 2)
        self.assertEqual(model.opt_solution[driver], ('0', '2'))
        self.assertEqual(model.opt_solution[driver2], ('0', '2'))
        self.assertEqual(model.opt_solution[driver3], ('0', '1', '2'))
        self.assertEqual(model.value, 8)


if __name__ == '__main__':
    unittest.main()
