# -*- coding: utf-8 -*-
# !/bin/env python

import logging
log = logging.getLogger('__name__')


def assert_paths_in_graph(paths, graph):
    count = {}
    for path, dct in paths.iteritems():
        for time, nb in dct.iteritems():
            count.setdefault((path[0], path[-1], time), 0)
            count[path[0], path[-1], time] += nb
        i = 0
        while i < len(path) - 1:
            node, next_node = path[i], path[i + 1]
            if not graph.hasNode(node):
                log.error("Node %s doesn't exist in graph %s", node, graph.name)
                raise KeyError("node %s doesn't exist in graph %s" % (node, graph.name))
            if not graph.hasEdge(node, next_node):
                log.error("Edge from %s to %s doesn't exist in graph %s", node, next_node, graph.name)
                raise KeyError("Edge from %s to %s doesn't exist in graph %s" % (node, next_node, graph.name))
            i += 1
        if not graph.hasNode(path[-1]):
            log.error("Node %s doesn't exist in graph %s", path[-1], graph.name)
            raise KeyError("node %s doesn't exist in graph %s" % (path[-1], graph.name))
    for (start, end, time), nb in count.iteritems():
        if nb != graph.getDrivers(start, end, starting_time=time):
            log.error("Drivers and path's flow don't match in graph %s", graph.name)
            raise Exception("Drivers and path's flow don't match in graph %s" % graph.name)


def get_id(obj):
    return hash(obj)
