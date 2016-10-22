# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import random

log = logging.getLogger(__name__)


class Graph(object):
    """ This class contains every instances and methods describing a Graph for our problem
        For using the interface this class must inherits from Simulator
    """
    def __init__(self, name='graph'):
        self.__name = name
        # structure
        self.__nodes = {}
        self.__data = {}

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
            x, y = data.get('posx') or 0.0, data.get('posy') or 0.0
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

    def getNodesNumber(self):
        return len(self.__nodes)

    def getRandomNode(self, black_list=set()):
        r, i, node = random.randint(0, self.getNodesNumber() - len(black_list) - 1), 0, None
        for node in self.getAllNodes():
            if node not in black_list:
                if r == i:
                    return node
                i += 1

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ EDGES ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def hasEdge(self, source, target):
        return self.hasNode(source) and self.hasNode(target) and target in self.__nodes[source]

    def addEdge(self, source, target, **data):
        if self.hasNode(source) and self.hasNode(target):
            if not self.hasEdge(source, target):
                self.__nodes[source][target] = data
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
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def getAllStartingNodes(self):
        for start, end, _ in self.getAllDrivers():
            yield start

    def getAllEndingNodes(self):
        for start, end, _ in self.getAllDrivers():
            yield end

    def getAllEdgesIncidentTo(self, node):
        for edge in self.getAllEdges():
            if edge[1] == node:
                yield edge

    def getAllEdgesOutfrom(self, node):
        for edge in self.getAllEdges():
            if edge[0] == node:
                yield edge

    def hasSuccessors(self, node):
        return len(self.__nodes[node]) > 0

    def getSuccessors(self, node):
        for n in self.__nodes[node].iterkeys():
            yield n

    def getSuccessorsWithProperties(self, node, props={}):
        for n, ps in self.__nodes[node].iteritems():
            for prop in props:
                if prop in ps:
                    yield n
                    break

    def getPredecessors(self, node):
        for n in self.getAllNodes():
            if self.hasEdge(n, node):
                yield n

    def assertIsAdjacentEdgeTo(self, edge, next_edge):
        if not self.hasEdge(*next_edge):
            log.error("Edge from node %s to node %s doesn't exist in graph %s",
                      next_edge[0], next_edge[1], self.name)
            raise KeyError("Edge from node %s to node %s doesn't exist in graph %s"
                           % (next_edge[0], next_edge[1], self.name))
        if edge and edge[1] != next_edge[0]:
            log.error('Current edge %s and next edge %s are not adjacent in graph %s',
                      str(edge), str(next_edge), self.name)
            raise Exception('Current edge %s and next edge %s are not adjacent in graph %s'
                            % (str(edge), str(next_edge), self.name))

    def isEdgeInPath(self, edge, path):
        if self.hasEdge(*edge):
            for i in range(len(path) - 1):
                if path[i] == edge[0] and path[i + 1] == edge[1]:
                    return True
        return False

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ DATA ----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def addNodePosition(self, node, x, y):
        self.__data.setdefault(node, {})
        self.__data[node].update({'x': x, 'y': y})

    def getData(self, node):
        return self.__data.get(node, {})

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ ALGORITHMS ----------------------------------------
    # ----------------------------------------------------------------------------------------

    def djikstra(self, start, end, length=0):
        """ find every path from start with given length
            options `length`: if 0 stop when every nodes have been discovered.
                              if integer >= 0 stop when every path with given length has been discovered
        """
        if not self.hasNode(start):
            log.error("Node %s not in graph %s", start, self.name)
            raise KeyError("Node %s not in graph %s" % (start, self.name))
        # paths: each element is a tuple of nodes, the last one is the length of the path
        paths = {start: set([(start, 0,)])}

        # Set the distance for the start node to zero
        nexts = {0: set([start])}
        distances = [0]
        min_length = None

        # Unvisited nodes
        visited = set([start]) if length > 0 else set()

        while min_length is None or (len(distances) > 0 and distances[0] <= min_length + length):
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
                if length == 0:
                    visited.add(n)

                # compute new distance
                new_dist = d + self.getEdgeProperty(current, n, 'distance')
                if min_length is not None and new_dist > min_length + length:
                    continue
                if min_length is None and n == end:
                    min_length = new_dist

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

        return {n: set([path for path in ps if path[-2] == end]) for n, ps in paths.iteritems()}

    def getPathsFromTo(self, start, end, length=0):
        if not self.hasNode(end):
            log.error("Node %s not in graph %s", end, self.name)
            raise KeyError("Node %s not in graph %s" % (end, self.name))
        paths = self.djikstra(start, end, length=length).get(end) or {}
        for path in paths:
            yield path[:-1]

    def djikstra_rec(self, start, end, paths={}):
        if start != end:
            for n in self.getSuccessors(start):
                rec = False
                for path in paths.get(start, []):
                    if n not in path:
                        paths.setdefault(n, set())
                        if path + (n,) not in paths[n]:
                            paths[n].add(path + (n,))
                            rec = True
                if rec:
                    self.djikstra_rec(n, end, paths=paths)

    def getAllPathsWithoutCycle(self, start, end):
        paths = {start: set([(start,)])}
        self.djikstra_rec(start, end, paths=paths)
        return paths.get(end, set())
