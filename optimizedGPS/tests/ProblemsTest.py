# -*- coding: utf-8 -*-
# !/bin/env python

import unittest

from optimizedGPS import options
from optimizedGPS.data.data_generator import (
    generate_graph_from_file,
    generate_grid_data
)
from optimizedGPS.problems.Comparator import BoundsHandler, MultipleGraphComparator, ResultsHandler
from optimizedGPS.problems.Heuristics import ShortestPathHeuristic, ShortestPathTrafficFree, RealGPS
from optimizedGPS.problems.Models import BestPathTrafficModel, FixedWaitingTimeModel, TEGLinearCongestionModel
from optimizedGPS.structure import Driver


class ProblemsTest(unittest.TestCase):
    def setUp(self):
        self.graph0 = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)
        self.graph0.add_driver(Driver('1', '6', 0))
        self.graph0.add_driver(Driver('1', '6', 1))
        self.graph0.add_driver(Driver('1', '6', 1))
        self.graph0.add_driver(Driver('2', '6', 0))
        self.graph0.add_driver(Driver('2', '6', 2))
        self.graph0.add_driver(Driver('3', '6', 0))
        self.graph0.add_driver(Driver('3', '6', 1))
        self.graph0.add_driver(Driver('3', '6', 2))

        self.graph1 = generate_grid_data(length=3, width=5, graph_name='grid-graph-3-5-test')
        self.graph1.add_driver(Driver('n_0_0', 'n_2_4', 0))
        self.graph1.add_driver(Driver('n_0_0', 'n_2_4', 1))
        self.graph1.add_driver(Driver('n_0_0', 'n_2_4', 1))
        self.graph1.add_driver(Driver('n_0_1', 'n_2_4', 0))
        self.graph1.add_driver(Driver('n_0_1', 'n_2_4', 2))
        self.graph1.add_driver(Driver('n_1_0', 'n_2_4', 0))
        self.graph1.add_driver(Driver('n_1_0', 'n_2_4', 1))
        self.graph1.add_driver(Driver('n_1_0', 'n_2_4', 2))

    def testMultipleGraphComparator(self):
        comparator = MultipleGraphComparator()
        comparator.append_graphs(self.graph0, self.graph1)
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
        handler = BoundsHandler()
        handler.set_graph(graph)

        # add bounds
        handler.append_lower_bound(ShortestPathTrafficFree)
        handler.append_upper_bound(ShortestPathHeuristic)

        # bompute bounds
        handler.compute_bounds()

        self.assertGreaterEqual(handler.get_upper_bound(), handler.get_lower_bound())

    def testResultsHandler(self):
        handler = ResultsHandler()
        handler.append_graphs(self.graph0, self.graph1)

        handler.append_lower_bound(ShortestPathTrafficFree)
        handler.append_upper_bound(ShortestPathHeuristic)

        handler.append_algorithm(BestPathTrafficModel, timeout=2)
        handler.append_algorithm(FixedWaitingTimeModel, timeout=2)
        handler.append_algorithm(RealGPS, timeout=2)
        handler.append_algorithm(TEGLinearCongestionModel, timeout=2)

        results = handler.compare()

        for i in range(len(results)):
            graph, res = handler.graphs[i], results[i]
            self.assertGreaterEqual(res[options.LOWER_BOUND_LABEL], 0)
            self.assertGreaterEqual(res[options.UPPER_BOUND_LABEL], res[options.LOWER_BOUND_LABEL])
            for algo, rs in res.iteritems():
                if algo not in [options.LOWER_BOUND_LABEL, options.UPPER_BOUND_LABEL]:
                    self.assertIn(rs[2], ['SUCCESS', 'TIMEOUT'], 'FAILED for algo %s on graph %s' % (algo, graph))


if __name__ == '__main__':
    unittest.main()
