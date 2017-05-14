# -*- coding: utf-8 -*-
# !/bin/env python

# In this file we generate all kind of data: real one, random one, ...

import random
import math

from optimizedGPS.structure import GPSGraph
from optimizedGPS.structure import GraphMLParser
from optimizedGPS.structure import Driver
from optimizedGPS.structure import DriversGraph


def generate_grid_data(length=5, width=5, **kwargs):
    """
    build a grid where the top-links node has name node_0_0
    from a given node, the reachable nodes are the one to the right and at the bottom

    :param length: number of nodes + 1 from links to right
    :param width: number of nodes + 1 from top to bottom
    :param kwargs: further options
    :return: An GPSGraph instance
    """
    graph = GPSGraph(name=kwargs.get('graph_name') or 'graph-%s-%s' % (length, width))
    for i in range(length):
        for j in range(width):
            source = 'n_%s_%s' % (i, j)
            graph.add_node(source)
            if i < length - 1:
                target = 'n_%s_%s' % (i + 1, j)
                graph.add_node(target)
                graph.add_edge(source, target, distance=1.0)
                if j < width - 1:
                    target = 'n_%s_%s' % (i, j + 1)
                    graph.add_node(target)
                    graph.add_edge(source, target, distance=1.0)
            else:
                if j < width - 1:
                    target = 'n_%s_%s' % (i, j + 1)
                    graph.add_node(target)
                    graph.add_edge(source, target, distance=1.0)
    return graph


def generate_graph_from_file(file_loc, **kwargs):
    """
    Use the GraphMLParser to extract the graph from the given file

    :param file_loc: path to the file
    :param kwargs: further options
    :return: a GPSGraph instance
    """
    if file_loc.endswith('.graphml'):
        return GraphMLParser().parse(file_loc, **kwargs)
    return None


def generate_random_drivers(graph, total_drivers=10, av_drivers=3, seed=None):
    """
    Given a graph, we add total_drivers drivers as following:
      - we take uniformly at random a source node and a reachable target node from source node
      - we generate a random number of drivers taking using a gaussian center on av_drivers with 1 as variance
      - we add these generated drivers to the graph, until we reach total_drivers
      - If we get too many drivers, among the last added drivers, we remove some of them to get exactly the numberw
        we want

    :param graph: A GPSGraph instance
    :param total_drivers: int
    :param av_drivers: float
    :param seed: see random package
    :return: None
    """
    drivers_graph = DriversGraph()
    random.seed(seed)
    total = total_drivers
    while total > 0:
        # Pick a random start node and a random end node different of the start node
        start = graph.get_random_node(starting_node=True, seed=seed)
        end = graph.get_random_node(random_walk_start=start, seed=seed)
        # add some drivers from start to end
        nb = max(random.gauss(av_drivers, 1.), 0.0)
        nb = int(min(nb, total))
        for n in range(nb):
            starting_time = random.randint(0, int(math.log(nb)) + 1)
            drivers_graph.add_driver(Driver(start, end, starting_time))
        total -= nb
    return drivers_graph


def generate_test_graph(length=2, width=3):
    """
    Generate a grid graph with the given arguments
    Generate always the same drivers from nodes 'n_0_0', 'n_1_0' and 'n_0_1' to final node

    :param length: see generate_grid_data
    :param width: see generate_grid_data
    :return: a GPSGraph instance
    """
    graph = generate_grid_data(length=length, width=width, graph_name='graph-%s-%s-test' % (length, width))
    drivers_graph = DriversGraph()

    drivers_graph.add_driver(Driver('n_0_0', 'n_%s_%s' % (length - 1, width - 1), 0))
    drivers_graph.add_driver(Driver('n_0_0', 'n_%s_%s' % (length - 1, width - 1), 1))
    drivers_graph.add_driver(Driver('n_0_0', 'n_%s_%s' % (length - 1, width - 1), 1))
    drivers_graph.add_driver(Driver('n_0_1', 'n_%s_%s' % (length - 1, width - 1), 0))
    drivers_graph.add_driver(Driver('n_0_1', 'n_%s_%s' % (length - 1, width - 1), 2))
    drivers_graph.add_driver(Driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), 0))
    drivers_graph.add_driver(Driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), 1))
    drivers_graph.add_driver(Driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), 2))

    return graph, drivers_graph


def generate_grid_graph_random_driver(length=2, width=3, nb_drivers=10):
    """
    Generate a grid graph with the given length and width
    Generate random drivers using generate_random_drivers function

    :param length: see generate_grid_data
    :param width: see generate_grid_data
    :param nb_drivers: see generate_random_drivers. Coresponds to total_drivers argument
    :return:
    """
    name = 'grid-graph-%s-%s-%s' % (length, width, nb_drivers)
    graph = generate_grid_data(length=length, width=width, graph_name=name)
    drivers_graph = generate_random_drivers(graph, total_drivers=nb_drivers)
    return graph, drivers_graph
