# -*- coding: utf-8 -*-
# !/bin/env python

from optimizedGPS import options

from optimizedGPS.logger import configure

configure()

import unittest

from optimizedGPS.data.data_generator import (
    generate_graph_from_file,
    generate_grid_data,
    generate_test_graph
)
from optimizedGPS.problems.SearchProblem import BacktrackingSearch
from optimizedGPS.problems.Heuristics import ShortestPathHeuristic, AllowedPathsHeuristic, ShortestPathTrafficFree, RealGPS
from optimizedGPS.problems.Models import BestPathTrafficModel, FixedWaitingTimeModel
from optimizedGPS.problems.Comparator import BoundsHandler, Comparator, MultipleGraphComparator, ResultsHandler


class ProblemsTest(unittest.TestCase):

    def testSearchProblem(self):
        graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)

        graph.add_driver('1', '6', starting_time=0)
        graph.add_driver('1', '6', starting_time=1, nb=2)
        graph.add_driver('2', '6', starting_time=0)
        graph.add_driver('2', '6', starting_time=2)
        graph.add_driver('3', '6', starting_time=0)
        graph.add_driver('3', '6', starting_time=1)
        graph.add_driver('3', '6', starting_time=2)

        comparator = Comparator()
        comparator.setGraph(graph)
        comparator.appendAlgorithm(BacktrackingSearch)
        comparator.appendAlgorithm(ShortestPathHeuristic)

        results = comparator.compare()
        self.assertTrue(set(map(lambda el: el[2], results.itervalues())).issubset({'SUCCESS'}))

    def testMultipleGraphComparator(self):
        graph0 = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)
        graph0.add_driver('1', '6', starting_time=0)
        graph0.add_driver('1', '6', starting_time=1, nb=2)
        graph0.add_driver('2', '6', starting_time=0)
        graph0.add_driver('2', '6', starting_time=2)
        graph0.add_driver('3', '6', starting_time=0)
        graph0.add_driver('3', '6', starting_time=1)
        graph0.add_driver('3', '6', starting_time=2)

        length, width = 3, 5
        graph1 = generate_grid_data(length=length, width=width, graph_name='grid-graph-%s-%s-test' % (length, width))
        graph1.add_driver('n_0_0', 'n_2_4', starting_time=0)
        graph1.add_driver('n_0_0', 'n_2_4', starting_time=1, nb=2)
        # graph1.addDriver('n_0_1', 'n_2_4', starting_time=0)
        # graph1.addDriver('n_0_1', 'n_2_4', starting_time=2)
        # graph1.addDriver('n_1_0', 'n_2_4', starting_time=0)
        # graph1.addDriver('n_1_0', 'n_2_4', starting_time=1)
        # graph1.addDriver('n_1_0', 'n_2_4', starting_time=2)

        graphs = [graph0, graph1]

        comparator = MultipleGraphComparator()
        comparator.appendGraphs(*graphs)
        comparator.appendAlgorithm(BacktrackingSearch, timeout=2)
        comparator.appendAlgorithm(ShortestPathHeuristic, timeout=2)
        comparator.appendAlgorithm(AllowedPathsHeuristic, diff_length=1, timeout=2)
        comparator.appendAlgorithm(BestPathTrafficModel, timeout=2)
        comparator.appendAlgorithm(ShortestPathTrafficFree, timeout=2)

        results = comparator.compare()
        self.assertEqual(len(results), len(comparator.graphs))
        for i in range(len(results)):
            graph, res = comparator.graphs[i], results[i]
            for algo, rs in res.iteritems():
                self.assertIn(rs[2], ['SUCCESS', 'TIMEOUT'], 'FAILED for algo %s on graph %s' % (algo, graph))

    def testBoundHandler(self):
        graph = generate_grid_data()
        handler = BoundsHandler()
        handler.setGraph(graph)

        # add bounds
        handler.appendLowerBound(ShortestPathTrafficFree)
        handler.appendUpperBound(ShortestPathHeuristic)

        # bompute bounds
        handler.computeBounds()

        self.assertGreaterEqual(handler.getUpperBound(), handler.getLowerBound())

    def testResultsHandler(self):
        graph0 = generate_test_graph()
        graph1 = generate_test_graph(length=3, width=2)
        graphs = [graph0, graph1]

        handler = ResultsHandler()
        handler.appendGraphs(*graphs)

        handler.appendLowerBound(ShortestPathTrafficFree)
        handler.appendUpperBound(ShortestPathHeuristic)

        handler.appendAlgorithm(BacktrackingSearch, timeout=2)
        handler.appendAlgorithm(AllowedPathsHeuristic, diff_length=1, timeout=2)
        handler.appendAlgorithm(BestPathTrafficModel, timeout=2)
        handler.appendAlgorithm(FixedWaitingTimeModel, timeout=2)
        handler.appendAlgorithm(RealGPS, timeout=2)

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
