# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import math
import random
from collections import defaultdict

from networkx import DiGraph, number_connected_components

from constants import constants
from optimizedGPS import labels

__all__ = ["Graph"]

log = logging.getLogger(__name__)


class Graph(DiGraph):
    """
    This class represents the static part of the data.
    It inherits from networkx.DiGraph, so the created graph is always directed.

    **Example:**

    >>> from optimizedGPS import Graph
    >>>
    >>> graph = Graph(name='test')
    >>> graph.add_node('node0', 0, 1)  # Add node on position (0, 1)
    >>> graph.add_node('node1', 1, 1)  # Add node on position (1, 1)
    >>> graph.add_edge('node0', 'node1', 3, 2)  # Add an edge between 'node0' and 'node1' with 2 lanes and distance 3
    >>>
    >>> pos = graph.get_position('node0')  # get positions of node0
    >>> print "positions of %s: %s" % ('node0', str(pos))  #doctest: +NORMALIZE_WHITESPACE
    # positions of node0: (0, 1) #
    >>> length = graph.get_edge_length('node0', 'node1')  # get edge's length
    >>> print "length: %s" % length  #doctest: +NORMALIZE_WHITESPACE
    # length: 3 #
    """

    """
    Default properties when adding a node or an edge
    When adding node or edge, if these properties are not specified, the default one is added
    """
    PROPERTIES = {
        'edges': {
            labels.DISTANCE: constants[labels.DISTANCE],
            labels.LANES: constants[labels.LANES]
        },
        'nodes': {
            labels.LATITUDE: constants[labels.LATITUDE],
            labels.LONGITUDE: constants[labels.LONGITUDE]
        }
    }

    def __init__(self, name='graph', data=None, **attr):
        """
        Name of the graph
        """
        self.__name = name
        super(Graph, self).__init__(data=data, **attr)

    @property
    def name(self):
        return self.__name

    # ----------------------------------------------------------------------------------------
    # ------------------------------------- NODES --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def add_node(self, n, lat=None, lon=None, attr_dict=None, **attr):
        """
        Add `n` as node on position (`lat`, `lon`). Other attributes can also be added. It calls the super method
        networkx.DiGraph.add_node`

        If lon or lat are not specified we ad the default values given by labels

        n is the node to add

        * options:

            * ``lat=None``: The latitude of the added node. If not specified, the default value is added.
            * ``lon=None``: The longitude of the added node. If not specified, the default value is added.
            * ``attr_dict=None``: Other attributes to add.
            * ``**attr``: Other attributes to add.
        """
        props = {k: v for k, v in self.PROPERTIES['nodes'].iteritems()}
        if attr_dict is not None:
            props.update(attr_dict)
        props[labels.LATITUDE] = lat if lat is not None else props[labels.LATITUDE]
        props[labels.LONGITUDE] = lon if lon is not None else props[labels.LONGITUDE]
        super(Graph, self).add_node(n, attr_dict=props, **attr)

    def get_position(self, node):
        """
        returns the node's position if it exists, otherwise returns None

        :param node: a node
        """
        try:
            return self.node[node][labels.LATITUDE], self.node[node][labels.LONGITUDE]
        except KeyError:
            return None

    def get_random_node(self, black_list=set(), random_walk_start=None, seed=None,
                        starting_node=False, ending_node=False):
        """
        Pick uniformly at random among the graph's nodes (except among black_list nodes),
        respecting the following rules:

        * options:

            * ``black_list=set()``: These nodes are not visited and can't be returned
            * ``random_walk_start=None``: If it is a node in graph we generate a random number between 1 and n,
                    where n = len(self.nodes()). We do a uniform random walk from the given node,
                    and after n steps we return the current node.
            * ``seed=None``: see random.seed(seed)
            * ``starting_node=False``: if True, it returns a node which has successors.
            * ``ending_node=False``: if True, it returns a node which has predecessors.

        :return: A node with the wanted properties
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

    def add_edge(self, u, v, distance=None, lanes=None, attr_dict=None, **attr):
        """
        Add a directed edge between `u` and `v`. If one or both nodes don't exist, we add it before.
        It calls the super-method networkx.DiGraph.add_edge

        u and v are respectively the source and target nodes

        * options:

            * ``distance=None``: distance of the added edge. If None, we add the default value.
            * ``lanes=None``: number of lanes of the added edge. If None, we add the default value.
            * ``attr_dict=None``: Other attributes to add.
            * ``**attr``: Other attributes to add.
        """
        props = {labels.DISTANCE: self.get_edge_length(u, v), labels.LANES: self.PROPERTIES['edges'][labels.LANES]}
        if attr_dict is not None:
            props.update(attr_dict)
        props[labels.DISTANCE] = distance if distance is not None else props[labels.DISTANCE]
        props[labels.LANES] = lanes if lanes is not None else props[labels.LANES]
        super(Graph, self).add_edge(u, v, attr_dict=props, **attr)

    def get_edge_property(self, source, target, prop):
        """
        return the wanted property for the given edge
        return None if the edge doesn't exist

        :param source: source node
        :param target: target node
        :param prop: wanted property's keyword

        :return: the wanted property's value
        """
        if self.has_edge(source, target):
            return self.adj[source][target].get(prop)
        log.warning("No edge between nodes %s and %s in graph %s", source, target, self.name)
        return None

    def get_edge_length(self, source, target):
        """
        Compute the edge's length considering the longitude and latitude of source and target.
        If one of these data doesn't exist we return a DEFAULT_DISTANCE (see options.py).

        :param source: source node
        :param target: target node

        :return: a float representing the edge's length
        """
        sx, sy = self.get_position(source) or (None, None)
        tx, ty = self.get_position(target) or (None, None)
        if any(map(lambda x: x is None, [sx, sy, tx, ty])):
            return self.PROPERTIES['edges'][labels.DISTANCE]
        return math.sqrt((sy - sx) * (sy - sx) + (ty - tx) * (ty - tx))

    def set_edge_property(self, source, target, prop, value):
        """
        Set value to property in edge's properties' set

        :param source: source node
        :param target: target node
        :param prop: property key
        :param value: property value
        :return:
        """
        if self.has_edge(source, target):
            self.adj[source][target][prop] = value

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ OTHERS --------------------------------------------
    # ----------------------------------------------------------------------------------------

    def successors_with_property(self, node, props=set()):
        """
        iterator which yield only the successors' nodes which have one of the given properties

        * options:

            * ``props=set()``: set of properties that the returned nodes should have (one of them at least)

        :return: `node`'s successors with the given properties
        """
        for n in self.successors(node):
            for prop in props:
                if prop in self.adj[node][n]:
                    yield n
                    break

    def assert_is_adjacent_edge_to(self, edge, next_edge):
        """
        raise an Exception if next_edge is not adjacent to edge in graph

        :param edge: source edge
        :param next_edge: adjacent edge to `edge`
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
        """
        return True if edge belongs to path, else False

        :param edge: edge
        :param path: tuple of nodes
        :type path: tuple

        :return: boolean
        """
        if self.has_edge(*edge):
            for i in range(len(path) - 1):
                if path[i] == edge[0] and path[i + 1] == edge[1]:
                    return True
        return False

    @classmethod
    def iter_edges_in_path(cls, path):
        """
        iterate the edges in path, without considering whether the edge exists in current graph

        :param path: tuple of nodes
        :type path: tuple
        :return: an iterator
        """
        for i in range(len(path) - 1):
            yield path[i], path[i + 1]

    # ----------------------------------------------------------------------------------------
    # ------------------------------------ ALGORITHMS ----------------------------------------
    # ----------------------------------------------------------------------------------------

    def djikstra(self, start, end, length=0, edge_property=labels.DISTANCE, key=None, next_choice=None):
        """
        find every path from start with given length

        * options:

            * ``length=0``: if 0 stops when a path from start to end has been discovered (shortest path).
                            if length > 0 stop when every paths whose length is the shortest path's length + `length`
                                have been discovered
            * ``edge_property=labels.DISTANCE``: the property "dictance" we take from edge to compute the distance
            * ``key=None``: If not None, used to return the distance of each edge
            * ``next_choice=None``: next_choice always return True for the visited edges. If an edge has value False
                                    by next_choice, we can't visit it.

        :return: a dictionnary with length as key and associated set of paths as value
        """
        if not self.has_node(start):
            log.error("Node %s not in graph %s", start, self.name)
            raise KeyError("Node %s not in graph %s" % (start, self.name))
        # paths: each element is a tuple of nodes, the last one is the length of the path
        paths = {start: {(start, 0,)}}

        # function for getting the distance set
        if key is None:
            get_distance = lambda u, v: self.get_edge_property(u, v, edge_property)
        else:
            get_distance = key

        # function for choosing the next nodes
        if next_choice is None:
            is_selectable = lambda cur, nod: self.get_edge_property(cur, nod, edge_property) is not None
        else:
            is_selectable = next_choice

        # Set the distance for the start node to zero
        nexts = {0: {start}}
        distances = [0]
        min_length = None

        # Unvisited nodes
        visited = {start} if length > 0 else set()

        while nexts and (min_length is None or (len(distances) > 0 and distances[0] <= min_length + length)):
            # Pops a vertex with the smallest distance
            d = distances[0]
            current = nexts[d].pop()

            # remove nodes from nexts and distances
            if len(nexts[d]) == 0:
                del nexts[d]
                del distances[0]

            for n in self.successors_iter(current):
                # if visited, skip
                if n in visited or not is_selectable(current, n):
                    continue

                # else add t in visited
                if length == 0:
                    visited.add(n)

                # compute new distance
                new_dist = d + get_distance(current, n)
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

    def get_paths_from_to(self, start, end, length=0, edge_property=labels.DISTANCE, key=None, next_choice=None):
        """
        yield every path from start to end.
        To see details about the given parameters, give a look to Graph.djikstra

        :return: an iterator
        """
        if not self.has_node(end):
            log.error("Node %s not in graph %s", end, self.name)
            raise KeyError("Node %s not in graph %s" % (end, self.name))
        paths = self.djikstra(
            start, end, length=length, edge_property=edge_property, key=key, next_choice=next_choice
        ).get(end) or {}
        for path in paths:
            yield path[:-1]

    def get_shortest_path(self, start, end, edge_property=labels.DISTANCE, key=None, next_choice=None):
        """
        :param start: source node
        :param end: target node
        :param edge_property: value on edge to consider for computing the shortest path
        :param key: function for computing distance on each edge
        :param next_choice: the successors of a node are chosen following this rule

        :return: the shortest path between `start` and `end`
        """
        return self.get_paths_from_to(start, end, edge_property=edge_property, key=key, next_choice=next_choice).next()

    @classmethod
    def generate_path_from_edges(cls, start, end, edges):
        """
        Starting at `start` and ending at `end`, we build a path using only the edge in `edges`.
        It raises an Exception if no path can be built

        :param start: source node
        :param end: target node
        :param edges: list or set of edges

        :return: a tuple of nodes which represents a path
        """
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

    def belong_to_same_road(self, u0, v0, u1, v1):
        """
        We check the number of lanes and the name of both edges.
        If It is the same, we return True

        :return: boolean
        """
        params0 = self.get_edge_data(u0, v0)
        params1 = self.get_edge_data(u1, v1)
        if params0[labels.LANES] == params1[labels.LANES] and params0.get("name") == params1.get("name"):
            return True
        return False

    def simplify_graph(self):
        """
        This function delete every node with degree in = 1 and degree out = 1.
        Actually, it just keeps nodes which represents either a start or end point of the graph (degree 1)
        or a intersection between several roads (degree >= 3).
        """
        visited = set(self.nodes())
        while len(visited) > 0:
            node = visited.pop()
            # First remove edges with same start and same target
            if self.has_edge(node, node):
                self.remove_edge(node, node)
            succ, pred = self.successors(node), self.predecessors_iter(node)
            if len(set(succ).union(pred)) == 2:
                for p in pred:
                    for s in succ:
                        if s != p and self.belong_to_same_road(p, node, node, s):
                            params = self.get_edge_data(p, node)
                            params[labels.DISTANCE] += self.get_edge_property(node, s, labels.DISTANCE)
                            self.remove_edge(p, node)
                            self.remove_edge(node, s)
                            self.add_edge(p, s, **params)
            if self.degree(node) == 0:
                self.remove_node(node)

    def get_attribute(self, attr):
        """
        If Graph object has `attr` as attribute, we return the associated value, else None

        :param attr: object
        :return: object
        """
        return self.graph.get(attr)

    @classmethod
    def get_paths_from_continuous_edge_description(cls, start, end, edge_description):
        """
        From this edge description we build a set of paths and we associate to each path a coefficient representing
        the quantity of flow driving on it.
        We suppose that each path is without cycle

        :param start: node
        :param end: node
        :param edge_description: dictionary containing edge as key and a coefficient in (0,1] as value
        :return: dict
        """
        paths = defaultdict(lambda: defaultdict(lambda: 0))
        paths[start][(start,)] = 1
        next_nodes = {start}
        while len(next_nodes) > 0:
            node = next_nodes.pop()
            edges = {e: c for e, c in edge_description.iteritems() if e[0] == node}
            if len(edges) == 0:
                continue
            for path, coeff in paths[node].iteritems():
                while coeff > 0:
                    edge, c = edges.popitem()
                    if coeff >= c:
                        paths[edge[1]][path + (edge[1],)] = c
                        coeff -= c
                    else:
                        paths[edge[1]][path + (edge[1],)] = coeff
                        edges[edge] = c - coeff
                        coeff = 0
                    if edge[1] != end:
                        next_nodes.add(edge[1])
        return paths[end]
