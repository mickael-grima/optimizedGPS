# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import random
from networkx import DiGraph, number_connected_components

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

    def get_random_node(self, black_list=set(), random_walk_start=None, seed=None,
                        starting_node=False, ending_node=False):
        """ Pick uniformly at random among the graph's nodes (except among black_list nodes)
            If `random_walk_start` is a node in graph we generate a random number between 1 and len(nodes): n.
            We do a uniform random walk from the given node, and after n steps we return the current node

            if starting_node is True, we want a node which has successors
            if ending_node is True, we want a node which has predecessors
        """
        random.seed(seed)

        # If a starting random_walk node has been given
        if self.has_node(random_walk_start):
            n = random.randint(1, self.number_of_nodes())
            current_node = random_walk_start
            # We procceed the random walk
            while n > 0:
                succ = self.successors(current_node)
                if len(succ) == 0:
                    return current_node
                r, i, nb = random.randint(0, len(succ) - 1), 0, len(succ) - 1
                for node in succ:
                    # If the node is in black list we don't pick it
                    if node in black_list:
                        nb -= 1
                        r = min(r, nb)
                        continue
                    # if the node is a not a starting node we don't pick it
                    if starting_node:
                        try:
                            self.successors_iter(node).next()
                        except StopIteration:
                            nb -= 1
                            r = min(r, nb)
                            continue
                    # if the node is a not a starting node we don't pick it
                    if ending_node:
                        try:
                            self.predecessors_iter(node).next()
                        except StopIteration:
                            nb -= 1
                            r = min(r, nb)
                            continue
                    if i <= r:
                        current_node = node
                    i += 1
                n -= 1
            return current_node

        # Else we choose an other node uniformly at random
        nb = self.number_of_nodes() - 1
        if nb == 1:
            return self.nodes()[0]
        r, i, nod = random.randint(0, self.number_of_nodes() - 1), 0, None
        for node in self.nodes():
            if starting_node:
                try:
                    self.successors_iter(node).next()
                except StopIteration:
                    nb -= 1
                    r = min(r, nb)
                    continue
            # if the node is a not a starting node we don't pick it
            if ending_node:
                try:
                    self.predecessors_iter(node).next()
                except StopIteration:
                    nb -= 1
                    r = min(r, nb)
                    continue
            # If node is forbidden we don't pick it
            if node in black_list:
                nb -= 1
                r = min(r, nb)
                continue
            if i <= r:
                nod = node
            i += 1
        return nod

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
        paths = {start: {(start, 0,)}}

        # Set the distance for the start node to zero
        nexts = {0: {start}}
        distances = [0]
        min_length = None

        # Unvisited nodes
        visited = {start} if length > 0 else set()

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
        for path in self.djikstra_rec(start, end, paths={start: {(start,)}}):
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

    def generate_path_from_edges(self, start, end, edges):
        path = (start,)
        visited, count = set(), 0
        while path[-1] != end:
            found = False
            for edge in filter(lambda e: e not in visited, edges):
                if edge[0] == path[-1]:
                    path += (edge[1],)
                    visited.add(edge)
                    count += 1
                    found = True
                    break
            if found is False:
                log.error("the given list of edges doesn't define a path")
                raise Exception("the given list of edges doesn't define a path")
        if count != len(edges):
            log.warning("not every edges have been used for creating the returning path")
        return path

    def get_stats(self):
        """
        Return some stats about the graph:
           - how many nodes
           - how many edges
           - how many connected components
           - average degree
           - how many unique sens
           - how many double sens

        :return: a dictionary
        """
        return {
            'nodes': self.number_of_nodes(),
            'edges': self.number_of_edges(),
            'connected_components': number_connected_components(self.to_undirected()),
            'av_degree': sum(self.degree().itervalues()) / float(self.number_of_nodes()),
            'unique_sens': len(filter(lambda e: not self.has_edge(e[1], e[0]), self.edges())),
            'double_sens': len(filter(lambda e: self.has_edge(e[1], e[0]), self.edges()))
        }

