# -*- coding: utf-8 -*-
# !/bin/env python

from data_generator import generate_graph_from_file
from simulator.GPSSimulator import GPSSimulator
from structure.GraphMLParser import GraphMLParser
import random


def test_graphml_writer():
    graph = generate_graph_from_file('static/grid-graph-2-3-test.graphml')
    graph.addNodePosition('n0', 0, 0)
    graph.addNodePosition('n1', 100, 0)
    graph.addNodePosition('n2', 0, 100)
    graph.addNodePosition('n3', 100, 100)
    graph.addNodePosition('n4', 0, 200)
    graph.addNodePosition('n5', 100, 200)
    for s, t in graph.getAllEdges():
        graph.setEdgeProperty(s, t, 'width', random.randint(3, 10))
    # add drivers
    graph.addDriver('n0', 'n5', 0, nb=2)
    graph.addDriver('n2', 'n5', 1, nb=3)
    graph.addDriver('n2', 'n3', 1, nb=1)
    graph.addDriver('n4', 'n5', 2, nb=2)
    # get path for drivers
    paths = {
        ('n0', 'n2', 'n3', 'n5'): {0: 2},
        ('n2', 'n3', 'n5'): {1: 2},
        ('n2', 'n4', 'n5'): {1: 1},
        ('n2', 'n3'): {1: 1},
        ('n4', 'n5'): {2: 2}
    }
    simulator = GPSSimulator(graph, paths)

    simulator.next()
    simulator.next()

    GraphMLParser().write(simulator.graph, 'static/test_graphml_writer.graphml')


if __name__ == '__main__':
    test_graphml_writer()
