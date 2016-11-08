# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import random
from networkx import DiGraph

log = logging.getLogger(__name__)


class Graph(DiGraph):
    """ This class contains every instances and methods describing a Graph for our problem
        It inherits from networkx.DiGraph
    """
    def __init__(self, name='graph'):
        self.__name = name
        # structure
        self.__data = {}
        super(Graph, self).__init__()

    @property
    def name(self):
        return self.__name

    # ----------------------------------------------------------------------------------------
    # ------------------------------------- NODES --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def get_random_node(self, black_list=set()):
        """ Pick uniformly at random among the graph's nodes (except among black_list nodes)
        """
        r, i, node = random.randint(0, self.number_of_nodes() - len(black_list) - 1), 0, None
        for node in self.nodes():
            if node not in black_list:
                if r == i:
                    return node
                i += 1

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ EDGES ---------------------------------------------
    # ----------------------------------------------------------------------------------------

    def get_edge_property(self, source, target, prop):
        """ return the wanted property for the given edge
            return None if the edge doesn't exist
        """
        if self.has_edge(source, target):
            return self.adj[source][target].get(prop)
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return None

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def successors_with_property(self, node, props={}):
        """ iterator which yield only the successors' nodes which belongs one of the given properties
        """
        for n in self.successors(node):
            for prop in props:
                if prop in self.adj[node][n]:
                    yield n
                    break

    def assert_is_adjacent_edge_to(self, edge, next_edge):
        """ raise an Exception if next_edge is not adjacent to edge in graph
        """
        if not self.has_edge(*next_edge):
            log.error("Edge from node %s to node %s doesn't exist in graph %s",
                      next_edge[0], next_edge[1], self.name)
            raise KeyError("Edge from node %s to node %s doesn't exist in graph %s"
                           % (next_edge[0], next_edge[1], self.name))
        if edge and edge[1] != next_edge[0]:
            log.error('Current edge %s and next edge %s are not adjacent in graph %s',
                      str(edge), str(next_edge), self.name)
            raise Exception('Current edge %s and next edge %s are not adjacent in graph %s'
                            % (str(edge), str(next_edge), self.name))

    def is_edge_in_path(self, edge, path):
        """ return True if edge belongs to path, else False
        """
        if self.has_edge(*edge):
            for i in range(len(path) - 1):
                if path[i] == edge[0] and path[i + 1] == edge[1]:
                    return True
        return False

    def iter_edges_in_path(self, path):
        for i in range(len(path) - 1):
            yield path[i], path[i + 1]

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ DATA ----------------------------------------------
    # ----------------------------------------------------------------------------------------

    def add_node_position(self, node, x, y):
        """ Add position to node
        """
        self.__data.setdefault(node, {})
        self.__data[node].update({'x': x, 'y': y})

    def get_position(self, node):
        """ returns the node's position if it exists, otherwise returns None
        """
        try:
            return self.__data[node]['x'], self.__data[node]['y']
        except KeyError:
            return None

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ ALGORITHMS ----------------------------------------
    # ----------------------------------------------------------------------------------------

    def djikstra(self, start, end, length=0):
        """ find every path from start with given length
            options `length`: if 0 stops when a path from start to end has been discovered (shortest path).
                              if length > 0 stop when every paths whose length is the shortest path's length + length
                                  have been discovered

            TODO: make it an iterator
        """
        if not self.has_node(start):
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

            for n in self.successors_with_property(current, props={'distance'}):
                # if visited, skip
                if n in visited:
                    continue

                # else add t in visited
                if length == 0:
                    visited.add(n)

                # compute new distance
                new_dist = d + self.get_edge_property(current, n, 'distance')
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

    def djikstra_rec(self, start, end, paths={}):
        """ recursive version of djikstra algorithm
        """
        if start != end:
            for n in self.successors_iter(start):
                rec = False
                for path in paths.get(start, []):
                    if n not in path:
                        paths.setdefault(n, set())
                        if path + (n,) not in paths[n]:
                            paths[n].add(path + (n,))
                            rec = True
                            if n == end:
                                yield path + (n,)
                if rec:
                    for path in self.djikstra_rec(n, end, paths=paths):
                        yield path

    def get_all_paths_without_cycle(self, start, end):
        """ yield every path from start to end wthout cycle
        """
        for path in self.djikstra_rec(start, end, paths={start: set([(start,)])}):
            yield path

    def get_paths_from_to(self, start, end, length=0):
        """ yield every path from start to end
            length is to be used in the same way as for djikstra above
        """
        if not self.has_node(end):
            log.error("Node %s not in graph %s", end, self.name)
            raise KeyError("Node %s not in graph %s" % (end, self.name))
        paths = self.djikstra(start, end, length=length).get(end) or {}
        for path in paths:
            yield path[:-1]

    def get_shortest_path(self, start, end):
        return self.get_paths_from_to(start, end).next()
