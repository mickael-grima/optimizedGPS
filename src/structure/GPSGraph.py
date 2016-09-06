# -*- coding: utf-8 -*-
# !/bin/env python

from Edge import Edge
import logging
from logger import configure
from utils.tools import get_id

configure()
log = logging.getLogger(__name__)


class GPSGraph(object):
    """ This class contains every instances and methods describing a Graph for our problem
        For using the interface this class must inherits from Simulator
    """
    def __init__(self, name='graph'):
        self.__name = name
        self.__nodes = {}
        self.__edges = {}

    @property
    def name(self):
        return self.__name

    def addNode(self, node):
        node_id = get_id(node)
        self.__nodes[node_id] = node
        log.info("Node %s added in graph %s", node.name, self.name)

    def hasNode(self, node):
        node_id = get_id(node)
        if node_id not in self.__nodes:
            log.warning("Node with id %s doesn't exist in graph %s", node_id, self.name)
            return False
        return True

    def getNodeById(self, node_id):
        node = self.__nodes.get(node_id)
        if self.hasNode(node):
            return node
        return None

    def getNodesByName(self, node_name):
        for node_id, res in self.__nodes.iteritems():
            if node_name == res.name:
                yield res

    def removeNode(self, node):
        if self.hasNode(node):
            node_id = get_id(node)

            # We remove the edges with node as source or target
            edges = set()
            if node_id in self.__edges:
                edges = edges.union(map(lambda idd: (node_id, idd), self.__edges[node_id].iterkeys()))
            for source_id in self.__edges.iterkeys():
                if source_id != node_id and node_id in self.__edges[source_id]:
                    edges.add((source_id, node_id))
            for edge in edges:
                self.removeEdge(self.getNodeById(edge[0]), self.getNodeById(edge[1]))

            del self.__nodes[node_id]
            log.info("Node %s removed from graph %s", node.name, self.name)
            return True

        log.warning("No node called %s in the graph %s", node.name, self.name)
        return False

    def getAllNodes(self):
        return set([node for node in self.__nodes.itervalues()])

    def addEdge(self, source, target, **kwards):
        if self.hasNode(source) and self.hasNode(target):
            edge = Edge(source, target, **kwards)
            self.__edges.setdefault(get_id(source), {})
            self.__edges[get_id(source)][get_id(target)] = edge
            log.info("Edge %s added in graph %s", edge.name, self.name)
            return True
        return False

    def hasEdge(self, source, target):
        source_id, target_id = get_id(source), get_id(target)
        if self.hasNode(source_id) and self.hasNode(target_id):
            edge = self.__edges.get(source_id, {}).get(target_id)
            if edge is not None:
                return True
            log.warning("No edge between node %s and %s in graph %s", source.name, target.name, self.name)
        log.warning("Incident nodes %s and/or %s don't exist in graph %s", source.name, target.name, self.name)
        return False

    def getEdge(self, source, target):
        if self.hasEdge(source, target):
            return self.__edges[get_id(source)][get_id(target)]
        return None

    def removeEdge(self, source, target):
        source_id, target_id = get_id(source), get_id(target)
        if self.hasEdge(source, target):
            edge = self.__edges[source_id][target_id]
            del self.__edges[source_id][target_id]
            if not self.__edges[source_id]:
                del self.__edges[source_id]
            log.info("Edge %s removed from graph %s", edge.name, self.name)
            return True
        return False

    def getAllEdges(self):
        return set([edge for dct in self.__edges.itervalues() for edge in dct.itervalues()])
