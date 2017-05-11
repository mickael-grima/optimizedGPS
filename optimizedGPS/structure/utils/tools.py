# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


def congestion_function(traffic_limit=1, **parameters):
    """
    Return the congestion function for the given parameters

    * options:

        * ``traffic_limit=1``: traffic limit to consider
        * ``**parameters``: edge parameters

    :return: func
    """
    def func(x):
        if x < 0:
            log.error("Traffic negative")
            raise ValueError("Traffic negative")
        if x < traffic_limit:
            return traffic_limit
        return x ** 4 + 1
    return func


def assert_has_graph_GUI_infos(graph):
    """
    Raise an error if a node doesn't have a position

    :param graph: Graph instance
    """
    for node in graph.nodes():
        if graph.get_position(node) is None:
            log.error("Geometry data missing for node %s in graph %s", node, graph.name)
            raise Exception("Geometry data missing for node %s in graph %s" % (node, graph.name))
