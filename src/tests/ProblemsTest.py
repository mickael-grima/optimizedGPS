# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

from logger import configure

configure()

import unittest
from data_generator import generate_graph_from_file
from SearchProblem import BacktrackingSearch


class ProblemsTest(unittest.TestCase):

    def testSearchProblem(self):
        graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)

        graph.addDriver('1', '6', starting_time=0)
        graph.addDriver('1', '6', starting_time=1, nb=2)
        graph.addDriver('2', '6', starting_time=0)
        graph.addDriver('2', '6', starting_time=2)
        graph.addDriver('3', '6', starting_time=0)
        graph.addDriver('3', '6', starting_time=1)
        graph.addDriver('3', '6', starting_time=2)

        allowed_paths = []
        # for p in graph.getPathsFromTo('1', '6', length=5):
        #     allowed_paths.append(p)
        # for p in graph.getPathsFromTo('2', '6', length=5):
        #     allowed_paths.append(p)
        # for p in graph.getPathsFromTo('3', '6', length=5):
        #     allowed_paths.append(p)

        problem = BacktrackingSearch(graph, allowed_paths=allowed_paths)

        problem.simulate()
        print problem.current_value
        print problem.step
        print problem.cut


if __name__ == '__main__':
    unittest.main()
