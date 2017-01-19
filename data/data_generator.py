# -*- coding: utf-8 -*-
# !/bin/env python

# In this file we generate all kind of data: real one, random one, ...

from structure.GPSGraph import GPSGraph
from structure.GraphMLParser import GraphMLParser
import random


def generate_grid_data(length=5, width=5, **kwards):
    """ build a grid where the top-links node has name node_0_0
        from a given node, the reachable nodes are the one to the right and at the bottom
    """
    graph = GPSGraph(name=kwards.get('graph_name') or 'graph-%s-%s' % (length, width))
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


def generate_graph_from_file(file_loc, **kwards):
    if file_loc.endswith('.graphml'):
        return GraphMLParser().parse(file_loc, **kwards)
    return None


# TODO be sure end is reachable from start
def generate_random_drivers(graph, total_drivers=10, av_drivers=3, seed=None):
    random.seed(seed)
    total = total_drivers
    while total > 0:
        # Pick a random start node and a random end node different of the start node
        start = graph.get_random_node(starting_node=True, seed=seed)
        end = graph.get_random_node(random_walk_start=start, seed=seed)
        # add some drivers from start to end
        nb = max(random.gauss(av_drivers, 1.), 0.0)
        nb = int(min(nb, total))
        graph.add_driver(start, end, nb=nb)
        total -= nb


def generate_test_graph(length=2, width=3):
    """ Generate a grid graph with the given arguments
        give always the same drivers from nodes 'n_0_0', 'n_1_0' and 'n_0_1' to final node
    """
    graph = generate_grid_data(length=length, width=width, graph_name='graph-%s-%s-test' % (length, width))

    graph.add_driver('n_0_0', 'n_%s_%s' % (length - 1, width - 1), starting_time=0)
    graph.add_driver('n_0_0', 'n_%s_%s' % (length - 1, width - 1), starting_time=1, nb=2)
    graph.add_driver('n_0_1', 'n_%s_%s' % (length - 1, width - 1), starting_time=0)
    graph.add_driver('n_0_1', 'n_%s_%s' % (length - 1, width - 1), starting_time=2)
    graph.add_driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), starting_time=0)
    graph.add_driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), starting_time=1)
    graph.add_driver('n_1_0', 'n_%s_%s' % (length - 1, width - 1), starting_time=2)

    return graph


def generate_grid_graph_random_driver(length=2, width=3, nb_drivers=10):
    name = 'grid-graph-%s-%s-%s' % (length, width, nb_drivers)
    graph = generate_grid_data(length=length, width=width, graph_name=name)
    generate_random_drivers(graph, total_drivers=nb_drivers)
    return graph
