# -*- coding: utf-8 -*-
# !/bin/env python

import logging
log = logging.getLogger('__name__')


def assert_paths_in_graph(paths, graph, simulator_type=0):
    if simulator_type == 0:
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
                log.error("Drivers %s and path's flow don't match in graph %s. %s drivers, %s have a path",
                          str((start, end, time)), graph.name, graph.getDrivers(start, end, starting_time=time), nb)
                raise Exception("Drivers %s and path's flow don't match in graph %s. %s drivers, %s have a path"
                                % (str((start, end, time)), graph.name,
                                   graph.getDrivers(start, end, starting_time=time), nb))
    elif simulator_type == 1:
        for path in paths:
            i = 0
            while i < len(path) - 1:
                if not graph.hasEdge(path[i], path[i + 1]):
                    log.error("graph %s has not path %s", graph.name, str(path))
                    raise Exception("graph %s has not path %s" % (graph.name, str(path)))
                i += 1


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


def assert_file_location(fname, typ='picture'):
    if typ == 'picture':
        if not fname.startswith('static/pictures/'):
            log.error("Specified file has to be stored in static/pictures/ ."
                      " the specified location is %s instead",
                      fname)
            raise ValueError("Specified file has to be stored in static/pictures/ ."
                             " the specified location is %s instead"
                             % fname)
