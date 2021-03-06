# -*- coding: utf-8 -*-
# !/bin/env python

"""
This script allows to load graphml files and to convert it to Graph instance. The other way around is also possible.
"""

import logging
import math
from xml.dom import minidom

import yaml

from GPSGraph import GPSGraph
from utils.tools import assert_has_graph_GUI_infos
from optimizedGPS import options

__all__ = ["GraphMLParser"]

log = logging.getLogger(__name__)


class GraphMLParser(object):
    """
    This class allows to create graph from .graphml file or to write .graphml files from graphs
    """

    def __init__(self):
        config = yaml.load(open('%s/config.yml' % options.PACKAGE_PATH, 'r'))
        """
        Set of configurations needed for creating the .graphml file
        """
        self._conf = config.get('graphml', {})
        """
        Set of properties
        """
        self._props = config.get('properties', {})

    def set_head(self, head):
        try:
            self._conf['head'] = head
        except KeyError as e:
            log.error(e.message)
            raise KeyError(e.message)

    def set_attributes(self, attr):
        try:
            self._conf['attributes'] = attr
        except KeyError as e:
            log.error(e.message)
            raise KeyError(e.message)

    def set_keys(self, keys):
        try:
            self._conf['keys'] = keys
        except KeyError as e:
            log.error(e.message)
            raise KeyError(e.message)

    def add_key(self, key_id, attrs):
        try:
            self._conf['keys'][key_id] = attrs
        except KeyError as e:
            log.error(e.message)
            raise KeyError(e.message)

    @classmethod
    def create_element(cls, doc, element_name, **attributes):
        element = doc.create_element(element_name)
        for key, value in attributes.iteritems():
            if not isinstance(key, str) and not isinstance(key, unicode):
                log.error("following element (key) is not a string: element=%s, type=%s", key, type(key))
                raise TypeError("following element (key) is not a string: element=%s, type=%s" % (key, type(key)))
            if not isinstance(value, str) and not isinstance(value, unicode):
                log.error("following element (value) is not a string: element=%s, type=%s", value, type(value))
                raise TypeError("following element (value) is not a string: element=%s, type=%s" % (value, type(value)))
            element.setAttribute(key, value)
        return element

    def create_node_element(self, doc, node_name, **kwargs):
        node = self.create_element(doc, 'node', id=node_name)
        data = self.create_element(doc, 'data', key='d6')
        shape_node = self.create_element(doc, 'y:ShapeNode')

        # fill
        fill = self.create_element(doc, 'y:Fill', color='#FFCC00', transparent='false')
        shape_node.appendChild(fill)
        # shape
        shape = self.create_element(doc, 'y:Shape', type='ellipse')
        shape_node.appendChild(shape)
        # geometry
        x = str(kwargs.get('data', {}).get('x') or 0.0)
        y = str(kwargs.get('data', {}).get('y') or 0.0)
        node_size = self._conf['geometry']['node-size']
        geometry = self.create_element(doc, 'y:Geometry', height=str(node_size), width=str(node_size), x=x, y=y)
        shape_node.appendChild(geometry)

        data.appendChild(shape_node)
        node.appendChild(data)
        return node

    def create_edge_element(self, doc, source, target, **kwards):
        edge = self.create_element(doc, 'edge', source=source, target=target)
        data = self.create_element(doc, 'data', key='d10')
        line = self.create_element(doc, 'y:GenericEdge', configuration="com.yworks.edge.framed")

        # path
        path = self.create_element(doc, 'y:Path', sx=str(kwards.get('sx') or 0.0), sy=str(kwards.get('sy') or 0.0),
                                   tx=str(kwards.get('tx') or 0.0), ty=str(kwards.get('ty') or 0.0))
        line.appendChild(path)
        # linestyle
        linestyle = self.create_element(doc, 'y:LineStyle', color='#000000', type='line',
                                        width=kwards.get('width') or '1.0')
        line.appendChild(linestyle)
        #  arrows
        arrows = self.create_element(doc, 'y:Arrows', source='none', target='standard')
        line.appendChild(arrows)
        # label
        label = self.create_element(doc, 'y:EdgeLabel', alignment='center', configuration='AutoFlippingLabel',
                                    distance='2.0', fontFamily='Dialog', fontSize='12', fontStyle='plain',
                                    hasBackgroundColor='false', hasLineColor='false', modelName='custom',
                                    preferredPlacement='anywhere', ratio='0.5', textColor='#000000', visible='true')
        text = doc.createTextNode(str(kwards.get('traffic') or 0.0))
        label.appendChild(text)
        line.appendChild(label)
        # styleProperties
        styleprop = self.create_element(doc, 'y:StyleProperties')
        prop = self.create_element(doc, 'y:Property', name="FramedEdgePainter.fillColor", value=kwards.get('color'))
        prop.setAttribute('class', 'java.awt.Color')
        styleprop.appendChild(prop)
        line.appendChild(styleprop)

        data.appendChild(line)
        edge.appendChild(data)
        return edge

    def compute_edge_coords(self, graph, source, target):
        """
        Compute the coordinates of the edges between both source and target, and target and source.
        The edge's coordinates is the pair of edge's tail's coordinates and edge's head's coordinates.
        if there is only one edge from source to target return 0.0, 0.0, 0.0, 0.0
        otherwise we follow these rules:
            - the edge from left to rigth is always under the one from rigth to left
            - if both edges are vertical, the edge from bottom to top is always to the right

        :param graph: Graph
        :param source: source node
        :param target: target node

        :return: tuple
        """
        if graph.has_edge(target, source):
            node_size = self._conf['geometry']['node-size']
            sx, sy = graph.get_position(source) or (0.0, 0.0)
            tx, ty = graph.get_position(target) or (0.0, 0.0)
            dist = math.sqrt(2 * (tx - sx) * (tx - sx) + 2 * (ty - sy) * (ty - sy))
            Rsx = node_size / 2 * (tx + ty - sx - sy) / dist
            Rsy = node_size / 2 * (ty - tx + sx - sy) / dist
            Rtx = node_size / 2 * (ty - tx + sx - sy) / dist
            Rty = node_size / 2 * (sy + sx - ty - tx) / dist
            return Rsx, Rsy, Rtx, Rty
        return 0.0, 0.0, 0.0, 0.0

    def compute_edge_color(self, time_suppl):
        """
        Compute the color of edge. red means time_suppl = +infinity, green means time_suppl = 0

        :param time_suppl: it represents the time we need to road on edge minus the time we need to drive
                           without traffic

        :return: string (represents a color)
        """
        keys = sorted(self._props['traffics'].iterkeys(), reverse=True)
        for key in keys:
            if key <= time_suppl:
                return self._props['traffic-colors'][self._props['traffics'][key]]

    def write(self, graph, fname):
        """
        Create a file with name `fname` and extension .graphml from `graph`

        :param graph: Graph
        :param fname: file name
        :type fname: string
        """
        assert_has_graph_GUI_infos(graph)

        doc = minidom.Document()

        root = self.create_element(doc, 'graphml', **self._conf['attributes'])
        doc.appendChild(root)

        # We add the keys
        for key_id, attrs in self._conf['keys'].iteritems():
            key = self.create_element(doc, 'key', id=key_id, **attrs)
            root.appendChild(key)

        # create the graph element
        graph_node = self.create_element(doc, 'graph', id=graph.name, edgedefault='directed')
        root.appendChild(graph_node)

        # Add nodes
        for n in graph.nodes():
            node = self.create_node_element(doc, n, data=graph.get_position(n) or {})
            graph_node.appendChild(node)

        # Add edge
        for source, target in graph.edges():
            sx, sy, tx, ty = self.compute_edge_coords(graph, source, target)
            width = graph.get_edge_property(source, target, 'width') or 0.0
            # compute time_suppl
            traffic = graph.get_edge_property(source, target, 'traffic') or 0.0
            cong_func = graph.get_congestion_function(source, target)
            time_suppl = (cong_func(traffic) - cong_func(0.0)) / cong_func(0.0)
            color = self.compute_edge_color(time_suppl)
            # add edge
            edge = self.create_edge_element(doc, source, target, sx=str(sx), sy=str(sy), tx=str(tx), ty=str(ty),
                                            width=str(width), color=color,
                                            traffic=graph.get_edge_property(source, target, 'traffic'))
            graph_node.appendChild(edge)

        f = open(fname, 'w')
        f.write(doc.toprettyxml(indent='    '))

    @classmethod
    def parse(cls, fname, distance_factor=1.0, distance_default=0.0, traffic_limit=1):
        """
        read a .graphml file and convert it into a GPSGraph.

        * options:

            * ``distance_factor=1.0``:
            * ``distance_default=1.0``: default distance for edges if not given
            * ``traffic_limit=1``: traffic limit for edges if not given

        :return: :class:``GPSGraph <GPSGraph.GPSGraph>``
        """
        dom = minidom.parse(open(fname, 'r'))
        root = dom.getElementsByTagName("graphml")[0]
        graph = root.getElementsByTagName("graph")[0]

        name = fname.split('/')[-1]
        name = name[:-4] if name.endswith('.png') else name
        name = name[:-5] if name.endswith('.jpeg') else name
        name = name[:-8] if name.endswith('.graphml') else name

        g = GPSGraph(name=name)

        nodes = {}
        # Get nodes
        for node in graph.getElementsByTagName("node"):
            # We store in graph only the ellipse nodes
            for data in node.getElementsByTagName("data"):
                if data.getAttribute('key') == 'd6':
                    shapenode = data.getElementsByTagName("y:ShapeNode")[0]
                    shape = shapenode.getElementsByTagName("y:Shape")[0]
                    if shape.getAttribute("type") == "ellipse":
                        n = node.getElementsByTagName('y:NodeLabel')[0].childNodes[0].nodeValue.strip()
                        if len(str(n)) == 0:
                            n = node.getAttribute('id')
                        geometry = shapenode.getElementsByTagName("y:Geometry")[0]
                        g.add_node(n, float(geometry.getAttribute('x')), float(geometry.getAttribute('y')))
                        nodes[node.getAttribute('id')] = n

        # Get edges
        for edge in graph.getElementsByTagName("edge"):
            for data in edge.getElementsByTagName("data"):
                if data.getAttribute("key") == "d10":
                    gen = data.getElementsByTagName("y:GenericEdge")
                    if gen:
                        source = nodes[edge.getAttribute('source')]
                        target = nodes[edge.getAttribute('target')]
                        distance = distance_default or g.get_edge_length(source, target)
                        g.add_edge(source, target, distance=distance / distance_factor, traffic_limit=traffic_limit)

        return g
