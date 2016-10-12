# -*- coding: utf-8 -*-
# !/bin/env python

from data_generator import generate_graph_from_file
from simulator.GPSSimulator import GPSSimulator
from structure.GraphMLParser import GraphMLParser
import random


def test_graphml_writer():
    graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml')
    graph.addNodePosition('1', 0, 0)
    graph.addNodePosition('2', 100, 0)
    graph.addNodePosition('3', 0, 100)
    graph.addNodePosition('4', 100, 100)
    graph.addNodePosition('5', 0, 200)
    graph.addNodePosition('6', 100, 200)
    for s, t in graph.getAllEdges():
        graph.setEdgeProperty(s, t, 'width', random.randint(3, 10))
    # add drivers
    graph.addDriver('1', '6', 0, nb=2)
    graph.addDriver('3', '6', 1, nb=3)
    graph.addDriver('3', '4', 1, nb=1)
    graph.addDriver('5', '6', 2, nb=2)
    # get path for drivers
    paths = {
        ('1', '3', '4', '6'): {0: 2},
        ('3', '4', '6'): {1: 2},
        ('3', '5', '6'): {1: 1},
        ('3', '4'): {1: 1},
        ('5', '6'): {2: 2}
    }
    simulator = GPSSimulator(graph, paths)

    i = 0
    while simulator.has_next():
        simulator.next()
        i += 1
    print i

    # GraphMLParser().write(simulator.graph, 'static/test_graphml_writer.graphml')





if __name__ == '__main__':
    test_graphml_writer()
