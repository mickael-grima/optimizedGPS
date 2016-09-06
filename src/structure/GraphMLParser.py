# -*- coding: utf-8 -*-
# !/bin/env python

from xml.dom import minidom
import yaml
from GPSGraph import GPSGraph
import math


class GraphMLParser(object):

    def __init__(self):
        self._conf = yaml.load(open('graphml.yml', 'r')).get('graphml', {})
        self.traffics = {
            0: 'no-traffic',
            0.1: 'very-light-traffic',
            0.2: 'light-traffic',
            0.3: 'middle-light-traffic',
            0.4: 'middle-dense-traffic',
            0.5: 'dense-traffic',
            1: 'very-dense-traffic',
            5: 'traffic-jam',
            10: 'apocalyptic-traffic'
        }

    def set_head(self, head):
        self._conf['head'] = head

    def set_attributes(self, attr):
        self._conf['attributes'] = attr

    def set_keys(self, keys):
        self._conf['keys'] = keys

    def add_key(self, key_id, attrs):
        self._conf['keys'][key_id] = attrs

    def createElement(self, doc, element_name, **attributes):
        element = doc.createElement(element_name)
        for key, value in attributes.iteritems():
            element.setAttribute(key, value)
        return element

    def create_node_element(self, doc, node_name, **kwards):
        node = self.createElement(doc, 'node', id=node_name)
        data = self.createElement(doc, 'data', key='d6')
        shapeNode = self.createElement(doc, 'y:ShapeNode')

        # fill
        fill = self.createElement(doc, 'y:Fill', color='#FFCC00', transparent='false')
        shapeNode.appendChild(fill)
        # shape
        shape = self.createElement(doc, 'y:Shape', type='ellipse')
        shapeNode.appendChild(shape)
        # geometry
        x = str(kwards.get('data', {}).get(node_name, {}).get('geometry', {}).get('x') or 0.0)
        y = str(kwards.get('data', {}).get(node_name, {}).get('geometry', {}).get('y') or 0.0)
        node_size = self._conf['geometry']['node_size']
        geometry = self.createElement(doc, 'y:Geometry', height=str(node_size), width=str(node_size), x=x, y=y)
        shapeNode.appendChild(geometry)

        data.appendChild(shapeNode)
        node.appendChild(data)
        return node

    def create_edge_element(self, doc, source, target, **kwards):
        edge = self.createElement(doc, 'edge', source=source, target=target)
        data = self.createElement(doc, 'data', key='d10')
        line = self.createElement(doc, 'y:GenericEdge')

        # path
        path = self.createElement(doc, 'y:Path', sx=kwards.get('sx') or 0.0, sy=kwards.get('sy') or 0.0,
                                  tx=kwards.get('tx') or 0.0, ty=kwards.get('ty') or 0.0)
        line.appendChild(path)
        # linestyle
        linestyle = self.createElement(doc, 'y:LineStyle', color=kwards.get('color') or '#000000', type='line',
                                       width=kwards.get('width') or '1.0')
        line.appendChild(linestyle)
        #  arrows
        arrows = self.createElement(doc, 'y:Arrows', source='node', target='standard')
        line.appendChild(arrows)
        # label
        label = self.createElement(doc, 'y:EdgeLabel', alignment='center', configuration='AutoFlippingLabel',
                                   distance='2.0', fontFamily='Dialog', fontSize='12', fontStyle='plain',
                                   hasBackgroundColor='false', hasLineColor='false', modelName='custom',
                                   preferredPlacement='anywhere', ratio='0.5', textColor='#000000', visible='true')
        # labelModel
        labelmodel = self.createElement(doc, 'y:LabelModel')
        smartedgelabelmodel = self.createElement(doc, 'y:SmartEdgeLabelModel', autoRotationEnabled='false',
                                                 defaultAngle='0.0', defaultDistance='10.0')
        labelmodel.appendChild(smartedgelabelmodel)
        label.appendChild(labelmodel)
        # modelParameter
        modelparameter = self.createElement(doc, 'y:ModelParameter')
        smedmopa = self.createElement(doc, 'y:SmartEdgeLabelModelParameter', angle='0.0', distance='30.0',
                                      distanceToCenter='true', position='right', ratio='0.5', segment='0')
        modelparameter.appendChild(smedmopa)
        label.appendChild(modelparameter)
        # prefferedplacementdescriptor
        prplde = self.createElement(doc, 'y:PreferredPlacementDescriptor', angle='0.0', distance='-1.0',
                                    angleOffsetOnRightSide='0', angleRotationOnRightSide='co', side='anywhere',
                                    angleReference='absolute', frozen='true', placement='anywhere',
                                    sideReference='relative_to_edge_flow')
        label.appendChild(prplde)
        label.string = str(kwards.get('traffic')) or ''
        line.appendChild(label)

        data.appendChild(line)
        edge.appendChild(data)
        return edge

    def compute_edge_coords(self, graph, source, target):
        """ if there is only one edge from source to target return 0.0, 0.0, 0.0, 0.0
            otherwise we follow these rules:
                - the edge from left to rigth is always under the one from rigth to left
                - if both edges are vertical, the edge from bottom to top is always to the right
        """
        if graph.hasEdge(target, source):
            node_size = self._conf['geometry']['node_size']
            sx, sy = graph.getData(source).get('x') or 0.0, graph.getData(source).get('y') or 0.0
            tx, ty = graph.getData(target).get('x') or 0.0, graph.getData(target).get('y') or 0.0
            dist = math.sqrt(2 * (tx - sx) * (tx - sx) + 2 * (ty - sy) * (ty - sy))
            Rsx = sx + node_size * (tx + ty - sx - sy) / dist
            Rsy = sy + node_size * (ty - tx + sx - sy) / dist
            Rtx = tx + node_size * (ty - tx + sx - sy) / dist
            Rty = ty + node_size * (ty + tx - sy - sx) / dist
            return Rsx, Rsy, Rtx, Rty
        return 0.0, 0.0, 0.0, 0.0

    def compute_edge_color(self, time_suppl):
        """ time_suppl represents the time we need to road on edge minus the time we need to drive without circulation
            red means time_suppl = +infinity, green: time_suppl = 0
        """
        traffic_desc = self.traffics[time_suppl]
        return self._conf['traffic-colors'][traffic_desc]

    def write(self, graph, fname):
        """
        """
        doc = minidom.Document()
        for k, v in self._conf['head'].iteritems():
            doc.toxml('%s="%s"' % (k, v))

        root = self.createElement(doc, 'graphml', **self._conf['attributes'])
        doc.appendChild(root)

        # We add the keys
        for key_id, attrs in self._conf['keys'].iteritems():
            key = self.createElement(doc, 'key', id=key_id, **attrs)
            root.appendChild(key)

        # create the graph element
        graph_node = self.createElement(doc, 'graph', id=graph.name, edgedefault='directed')
        root.appendChild(graph_node)

        # Add nodes
        for n in graph.getAllNodes():
            node = self.create_node_element(doc, n, data=graph.getData(n))
            graph_node.appendChild(node)

        # Add edge
        for source, target in graph.getAllEdges():
            sx, sy, tx, ty = self.compute_edge_coords(doc, graph, source, target)
            width = graph.getEdgeProperty(source, target, 'width') or 0.0
            # compute time_suppl
            traffic = graph.getEdgeProperty(source, target, 'traffic') or 0.0
            cong_func = graph.getCongestionFunction(source, target)
            time_suppl = cong_func(traffic) / cong_func(0.0)
            color = self.compute_edge_color(time_suppl)
            # add edge
            edge = self.create_edge_element(doc, source, target, sx=sx, sy=sy, tx=tx, ty=ty, width=width, color=color)
            graph_node.appendChild(edge)

        f = open(fname, 'w')
        f.write(doc.toprettyxml(indent='    '))

    def parse(self, fname):
        """
        """
        dom = minidom.parse(open(fname, 'r'))
        root = dom.getElementsByTagName("graphml")[0]
        graph = root.getElementsByTagName("graph")[0]
        name = graph.getAttribute('id')

        g = GPSGraph(name=name)

        # Get nodes
        for node in graph.getElementsByTagName("node"):
            # We store in graph only the ellipse nodes
            for data in node.getElementsByTagName("data"):
                if data.getAttribute('key') == 'd6':
                    shapenode = data.getElementsByTagName("y:ShapeNode")[0]
                    shape = shapenode.getElementsByTagName("y:Shape")[0]
                    if shape.getAttribute("type") == "ellipse":
                        n = node.getAttribute('id')
                        geometry = shapenode.getElementsByTagName("y:Geometry")[0]
                        g.addNode(n, geometry={'x': geometry.getAttribute('x'),
                                               'y': geometry.getAttribute('y')})

        # Get edges
        for edge in graph.getElementsByTagName("edge"):
            for data in edge.getElementsByTagName("data"):
                if data.getAttribute("key") == "d10":
                    if data.getElementsByTagName("y:PolyLineEdge"):
                        source = edge.getAttribute('source')
                        target = edge.getAttribute('target')
                        g.addEdge(source, target)

        return g
