# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__))[:-5])

from logger import configure

configure()

import unittest
from structure.data_generator import generate_graph_from_file, generate_grid_data, generate_random_drivers
from problems.SearchProblem import BacktrackingSearch
from problems.Heuristics import ShortestPathHeuristic, AllowedPathsHeuristic
from problems.Models import ContinuousTimeModel
from Comparator import Comparator, MultipleGraphComparator


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

        comparator = Comparator()
        comparator.setGraph(graph)
        comparator.appendAlgorithm(BacktrackingSearch)
        comparator.appendAlgorithm(ShortestPathHeuristic)

        print comparator.compare()

    def testMultipleGraphComparator(self):
        graph0 = generate_graph_from_file('static/grid-graph-2-3-test.graphml', distance_default=1.0)
        graph0.addDriver('1', '6', starting_time=0)
        graph0.addDriver('1', '6', starting_time=1, nb=2)
        graph0.addDriver('2', '6', starting_time=0)
        graph0.addDriver('2', '6', starting_time=2)
        graph0.addDriver('3', '6', starting_time=0)
        graph0.addDriver('3', '6', starting_time=1)
        graph0.addDriver('3', '6', starting_time=2)

        graph1 = generate_grid_data(length=3, width=5, graph_name='graph1')
        graph1.addDriver('n_0_0', 'n_2_4', starting_time=0)
        graph1.addDriver('n_0_0', 'n_2_4', starting_time=1, nb=2)
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
        comparator.appendAlgorithm(ContinuousTimeModel, timeout=2)

        print comparator.compare()


if __name__ == '__main__':
    unittest.main()
