# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


def splitObjectsInBoxes(boxes, nb):
    """ split nb in the boxes. Yield every possibilities
    """
    pass


def get_id(obj):
    return hash(obj)


def assert_paths_in_graph(graph, *paths):
    for path in paths:
        i = 0
        while i < len(path) - 1:
            if not graph.hasEdge(path[i], path[i + 1]):
                log.error("graph %s has not path %s", graph.name, str(path))
                raise Exception("graph %s has not path %s" % (graph.name, str(path)))
