# -*- coding: utf-8 -*-
# !/bin/env python

# In this file we generate all kind of data: real one, random one, ...

from structure.GPSGraph import GPSGraph
from structure.GraphMLParser import GraphMLParser


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
