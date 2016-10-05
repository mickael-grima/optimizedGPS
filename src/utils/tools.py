# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


def splitObjectsInBoxes(nb_boxes, nb):
    """ split nb in the boxes. Yield every possibilities
        boxes is a list of container's capacities

        IMPORTANT: we need here an iterator
    """
    if nb_boxes < 0 or nb < 0:
        log.error("argument non valid: nb_boxes=%s, nb=%s", nb_boxes, nb)
        raise Exception("argument non valid: nb_boxes=%s, nb=%s" % (nb_boxes, nb))
    if nb_boxes > 0:
        if nb_boxes == 1:
            yield (nb,)
        elif nb == 0:
            yield tuple([0 for _ in range(nb_boxes)])
        else:
            i = int(nb / nb_boxes)
            while i >= 0:
                for sol in splitObjectsInBoxes(nb_boxes - 1, nb - i):
                    yield (i,) + sol
                i -= 1
            i = int(nb / nb_boxes) + 1
            while i <= nb:
                for sol in splitObjectsInBoxes(nb_boxes - 1, nb - i):
                    yield (i,) + sol
                i += 1


def get_id(obj):
    return hash(obj)


def assert_paths_in_graph(graph, *paths):
    for path in paths:
        i = 0
        while i < len(path) - 1:
            if not graph.hasEdge(path[i], path[i + 1]):
                log.error("graph %s has not path %s", graph.name, str(path))
                raise Exception("graph %s has not path %s" % (graph.name, str(path)))
            i += 1
