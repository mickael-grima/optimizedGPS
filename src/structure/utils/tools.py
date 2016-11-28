# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


def congestion_function(traffic_limit=1, **parameters):
    def func(x):
        if x < 0:
            log.error("Traffic negative")
            raise ValueError("Traffic negative")
        if x <= traffic_limit:
            return x
        return x
    return func


def assert_has_graph_GUI_infos(graph):
    for node in graph.nodes():
        if graph.get_position(node) is None:
            log.error("Geometry data missing for node %s in graph %s", node, graph.name)
            raise Exception("Geometry data missing for node %s in graph %s" % (node, graph.name))
