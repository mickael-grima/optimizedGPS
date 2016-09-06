# -*- coding: utf-8 -*-
# !/bin/env python

import logging

log = logging.getLogger(__name__)


class GPSGraph(object):
    """ This class contains every instances and methods describing a Graph for our problem
        For using the interface this class must inherits from Simulator
    """
    def __init__(self, name='graph'):
        self.__name = name
        # structure
        self.__nodes = {}
        self.__data = {}
        # drivers
        self.__drivers = {}

    @property
    def name(self):
        return self.__name

    # ----------------------------------------------------------------------------------------
    # ------------------------------------- NODES --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def hasNode(self, node):
        if node not in self.__nodes:
            return False
        return True

    def addNode(self, node, **data):
        if not self.hasNode(node):
            self.__nodes[node] = {}
            x, y = data.get('geometry', {}).get('x') or 0.0, data.get('geometry', {}).get('y') or 0.0
            self.addNodePosition(node, x, y)
            log.info("Node %s added in graph %s", node, self.name)
            return True
        return False

    def removeNode(self, node):
        if self.hasNode(node):
            # We remove the edges with node as source or target
            while self.__nodes[node]:
                self.removeEdge(node, self.__nodes[node].popitem()[0])
            del self.__nodes[node]
            for source in self.getAllNodes():
                if node in self.__nodes[source]:
                    self.removeEdge(source, node)
            log.info("Node %s removed from graph %s", node, self.name)
            return True
        log.warning("No node called %s in the graph %s", node, self.name)
        return False

    def getAllNodes(self):
        return self.__nodes.iterkeys()

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ EDGES ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def hasEdge(self, source, target):
        return self.hasNode(source) and self.hasNode(target) and target in self.__nodes[source]

    def addEdge(self, source, target, **kwards):
        if self.hasNode(source) and self.hasNode(target):
            if not self.hasEdge(source, target):
                self.__nodes[source][target] = kwards
                log.info("Edge added between nodes %s and %s in graph %s", source, target, self.name)
                return True
            log.warning("Edge already exists between nodes %s and %s in graph %s", source, target, self.name)
            return False
        log.warning("No node %s or %s in graph %s", source, target, self.name)
        return False

    def hasProperty(self, source, target, prop):
        if self.hasEdge(source, target):
            return prop in self.__nodes[source][target]
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return False

    def getEdgeProperties(self, source, target):
        return self.__nodes.get(source, {}).get(target)

    def getEdgeProperty(self, source, target, prop):
        if self.hasEdge(source, target):
            return self.__nodes[source][target].get(prop)
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return None

    def setEdgeProperty(self, source, target, prop, value):
        if self.hasEdge(source, target):
            self.__nodes[source][target][prop] = value
            log.info('property %s set to value %s for edge (%s,%s) in graph %s',
                     prop, str(value), source, target, self.name)
            return True
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return False

    def removeEdge(self, source, target):
        if self.hasEdge(source, target):
            del self.__edges[source][target]
            log.info("Edge between nodes %s and %s removed from graph %s", source, target, self.name)
            return True
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return False

    def getAllEdges(self):
        for source, dct in self.__nodes.iteritems():
            for target in dct.iterkeys():
                yield (source, target)

    # ----------------------------------------------------------------------------------------
    # ---------------------------------- DRIVERS ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def hasDriver(self, start, end):
        return self.hasNode(start) and self.hasNode(end) and self.__drivers.get(start, {}).get(end) is not None

    def addDriver(self, start, end):
        if self.hasNode(start) and self.hasNode(end):
            self.__drivers.setdefault(start, {})
            self.__drivers[start].setdefault(end, 0)
            self.__drivers[start][end] += 1
            log.info("Driver from %s to %s added to graph %s", start, end, self.name)
            return True
        log.warning("Node %s or %s doesn't exist in graph %s", start, end, self.name)
        return False

    def getAllDrivers(self):
        for start, dct in self.__drivers.iteritems():
            for end, nb in dct.iteritems():
                yield (start, end), nb

    def getAllDriversFromStartingNode(self, start):
        for end, nb in self.__drivers.get(start, {}).iteritems():
            yield (start, end), nb

    def getAllDriversToEndingNode(self, end):
        for start, dct in self.__drivers.iteritems():
            for e, nb in dct.iteritems():
                if e == end:
                    yield (start, end), nb

    def removeDriver(self, start, end):
        if self.hasDriver(start, end):
            self.__drivers[start][end] -= 1
            if self.__drivers[start][end] == 0:
                del self.__drivers[start][end]
            if not self.__drivers[start]:
                del self.__drivers[start]
            log.info("driver removed from %s to %s in graph %s", start, end, self.name)
            return True
        log.warning("No driver from %s to %s in graph %s", start, end, self.name)
        return False

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def getAllStartingNodes(self):
        for (start, end), _ in self.getAllDrivers():
            yield start

    def getAllEndingNodes(self):
        for (start, end), _ in self.getAllDrivers():
            yield end

    def getAllEdgesIncidentTo(self, node):
        for edge in self.getAllEdges():
            if edge[1] == node:
                yield edge

    def getAllEdgesOutfrom(self, node):
        for edge in self.getAllEdges():
            if edge[0] == node:
                yield edge

    def getSuccessors(self, node):
        for n in self.__nodes[node].iterkeys():
            yield n

    def getSuccessorsWithProperties(self, node, props={}):
        for n, ps in self.__nodes[node].iteritems():
            for prop in props:
                if prop in ps:
                    yield n
                    break

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ DATA ----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def addNodePosition(self, node, x, y):
        self.__data.setdefault(node, {})
        self.__data[node]['geometry'] = {'x': x, 'y': y}

    def getData(self, node):
        return self.__data.get(node, {})

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ ALGORITHMS ----------------------------------------
    # ----------------------------------------------------------------------------------------

    def djikstra(self, start, length='min'):
        """ find every path from start with given length
            options `length`: if 'min' stop when every nodes have been discovered.
                              if integer >= 0 stop when every path with given length has been discovered
        """
        # paths: each element is a tuple of nodes, the last one is the length of the path
        paths = {start: set([(start, 0,)])}

        # Set the distance for the start node to zero
        nexts = {0: set([start])}
        distances = [0]

        # Unvisited nodes
        visited = set([start]) if length == 'min' else set()

        while len(distances) and distances[0] <= length:
            # Pops a vertex with the smallest distance
            d = distances[0]
            current = nexts[d].pop()

            # remove nodes from nexts and distances
            if len(nexts[d]) == 0:
                del nexts[d]
                del distances[0]

            for n in self.getSuccessorsWithProperties(current, props={'distance'}):
                # if visited, skip
                if n in visited:
                    continue

                # else add t in visited
                if length == 'min':
                    visited.add(n)

                # compute new distance
                new_dist = d + self.getEdgeProperty(current, n, 'distance')
                if new_dist > length:
                    continue

                # add new node in nexts and distances
                nexts.setdefault(new_dist, set())
                nexts[new_dist].add(n)
                i = 0
                while i < len(distances):
                    if distances[i] == new_dist:
                        i = -1
                        break
                    elif distances[i] > new_dist:
                        break
                    i += 1
                if i >= 0:
                    distances.insert(i, new_dist)

                # update paths
                paths.setdefault(n, set())
                for p in paths[current]:
                    if p[-1] == d:
                        paths[n].add(p[:-1] + (n, new_dist,))

        return paths

    def getPathsFromTo(self, start, end, length='min'):
        paths = self.djikstra(start, length=length).get(end) or {}
        if type(length) == int:
            for path in paths:
                yield path[:-1]
        elif length == 'min':
            yield min(paths, key=lambda path: path[-1])[:-1]
