# -*- coding: utf-8 -*-
# !/bin/env python

# In this file we generate all kind of data: real one, random one, ...

from structure.GPSGraph import GPSGraph
from structure.GraphMLParser import GraphMLParser
import random


def generate_grid_data(length=5, width=5, **kwards):
    """ build a grid where the top-links node has name Node_0_0
        from a given node, the reachable nodes are the one to the right at the bottom
    """
    graph = GPSGraph(name=kwards.get('graph_name') or 'graph')
    for i in range(length):
        for j in range(width):
            graph.addNode('node_%s_%s' % (i, j))
            if i < length - 1:
                graph.addNode('node_%s_%s' % (i + 1, j))
                graph.addEdge('node_%s_%s' % (i, j), 'node_%s_%s' % (i + 1, j), size=10)
                if j < width - 1:
                    graph.addNode('node_%s_%s' % (i, j + 1))
                    graph.addEdge('node_%s_%s' % (i, j), 'node_%s_%s' % (i, j + 1), size=10)
            else:
                if j < width - 1:
                    graph.addNode('node_%s_%s' % (i, j + 1))
                    graph.addEdge('node_%s_%s' % (i, j), 'node_%s_%s' % (i, j + 1), size=10)
    return graph


def generate_graph_from_file(file_loc):
    if file_loc.endswith('.graphml'):
        return GraphMLParser().parse(file_loc)
    return None


def generate_random_drivers(graph, total_drivers=10, nb_drivers=3):
    total = total_drivers
    while total > 0:
        # Pick a random start node and a random end node different of the start node
        start = graph.getRandomNode()
        end = graph.getRandomNode(black_list={start})
        # add some drivers from start to end
        nb = max(random.gauss(nb_drivers, 1.), 0.0)
        nb = int(min(nb, total))
        graph.addDriver(start, end, nb=nb)
        total -= nb
    return graph
