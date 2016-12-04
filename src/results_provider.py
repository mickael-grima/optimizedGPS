# -*- coding: utf-8 -*-
# !/bin/env python

from logger import configure
from problems.Comparator import ResultsHandler
from problems.Models import BestPathTrafficModel
from structure.data_generator import generate_grid_graph_random_driver

configure()


def get_results_for_grid_graph():
    # create the results handler
    results_handler = ResultsHandler()

    # set the bounds and algorithm
    results_handler.appendAlgorithm(BestPathTrafficModel)

    # append the graphs
    for length in range(3, 10):
        for width in range(3, 10):
            for driver in range(10, 100, 10):
                graph = generate_grid_graph_random_driver(length=length, width=width, nb_drivers=driver)
                results_handler.appendGraphs(graph)

    # write in a file
    results_handler.writeIntoFile(results_handler.compare())


if __name__ == '__main__':
    get_results_for_grid_graph()
