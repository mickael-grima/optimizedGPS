# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


def congestion_function(**parameters):
    if 'a' in parameters:
        if 'b' in parameters:
            return lambda x: parameters['a'] * x * x * x * x + parameters['b']
        else:
            return lambda x: parameters[0] * x * x * x * x + 1
    else:
        return lambda x: x * x * x * x + 1


def assert_has_graph_GUI_infos(graph):
    for node in graph.getAllNodes():
        if 'x' not in graph.getData(node) or 'y' not in graph.getData(node):
            log.error("Geometry data missing for node %s in graph %s", node, graph.name)
            raise Exception("Geometry data missing for node %s in graph %s" % (node, graph.name))
