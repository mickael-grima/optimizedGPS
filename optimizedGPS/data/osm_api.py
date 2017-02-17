# -*- coding: utf-8 -*-
# !/bin/env python

"""
    Here we find everything related to the osm api
"""

import urllib2
from xml.dom import minidom

from api import API
from optimizedGPS import labels
from optimizedGPS.structure import GPSGraph
from utils.files_manager import __get_data_from_file__, __write_data_to_file__
from utils.format_manager import __check_call_api_format__

__all__ = ["RoadMapper"]


class OSMXAPI(API):
    TAGS = {
        'motorway': {
            labels.LANES: 2,
            labels.MAX_SPEED: 130
        },
        'trunk': {
            labels.LANES: 2,
            labels.MAX_SPEED: 110
        },
        'primary': {
            labels.LANES: 2,
            labels.MAX_SPEED: '50|90'
        },
        'secondary': {
            labels.LANES: 2,
            labels.MAX_SPEED: '50|90'
        },
        'tertiary': {
            labels.LANES: 2,
            labels.MAX_SPEED: '50|90'
        },
        'unclassified': {
            labels.LANES: 1,
            labels.MAX_SPEED: 50
        },
        'residential': {
            labels.LANES: 1,
            labels.MAX_SPEED: 50
        },
        'motorway_link': {
            labels.LANES: 1,
            labels.MAX_SPEED: 130
        },
        'motorway_junction': {
            labels.LANES: 1,
            labels.MAX_SPEED: 130
        },
        'trunk_link': {
            labels.LANES: 1,
            labels.MAX_SPEED: 110
        },
        'primary_link': {
            labels.LANES: 1,
            labels.MAX_SPEED: '50|90'
        },
        'secondary_link': {
            labels.LANES: 1,
            labels.MAX_SPEED: '50|90'
        },
        'tertiary_link': {
            labels.LANES: 1,
            labels.MAX_SPEED: '50|90'
        },
        'living_street': {
            labels.LANES: 1,
            labels.MAX_SPEED: 20
        },
        'road': {
            labels.LANES: 1,
            labels.MAX_SPEED: '50|90'
        }
    }

    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat):
        # roads
        url = "%s?way[highway=*][bbox=%s]" % (self.url, ','.join([min_lon, min_lat, max_lon, max_lat]))
        res_ways = urllib2.urlopen(url)
        # nodes
        url = "%s?node[bbox=%s]" % (self.url, ','.join([min_lon, min_lat, max_lon, max_lat]))
        res_nodes = urllib2.urlopen(url)
        return self.read_xml(res_ways.read(), res_nodes.read())

    @classmethod
    def read_xml(cls, xml_roads, xml_nodes):
        dom_r = minidom.parseString(xml_roads)
        dom_n = minidom.parseString(xml_nodes)
        return (
            cls.extract_roads(dom_r.getElementsByTagName('way')),
            cls.extract_nodes(dom_n.getElementsByTagName('node'))
        )

    @classmethod
    def extract_roads(cls, ways):
        roads = []
        for way in ways:
            save, road = False, {'nodes': [], 'params': {}}
            # Parse the tags and check we got a wanted road
            for tag in way.getElementsByTagName('tag'):
                if tag.getAttribute('k') == 'highway':
                    if tag.getAttribute('v') in cls.TAGS:
                        save = True
                        road['params']['highway'] = tag.getAttribute('v')
                    else:
                        break
                else:
                    road['params'][tag.getAttribute('k')] = tag.getAttribute('v')
            if save:
                for node in way.getElementsByTagName('nd'):
                    road['nodes'].append(node.getAttribute('ref'))
                roads.append(road)
        return roads

    @classmethod
    def extract_nodes(cls, nodes):
        nds = []
        for node in nodes:
            lon = node.getAttribute('lon')
            lat = node.getAttribute('lat')
            idd = node.getAttribute('id')
            nds.append({labels.LONGITUDE: lon, labels.LATITUDE: lat, 'id': idd})
        return nds


class RoadMapper(OSMXAPI):
    def convert_into_graph(self, roads, nodes):
        """
        Convert the map to a GPSGraph

        :param road_map: map gotten by getRoadMap method
        :return: a GPSGraph object
        """
        graph = GPSGraph()
        # First add the nodes
        for node in nodes:
            node_id, lat, lon = node['id'], node[labels.LATITUDE], node[labels.LONGITUDE]
            graph.add_node(node_id, lat, lon)
        # Then add the edges between nodes
        for road in roads:
            typ = road.pop('highway')
            road[labels.LANES] = road.get(labels.LANES) or self.TAGS[typ][labels.LANES]
            road[labels.MAX_SPEED] = road.get(labels.MAX_SPEED) or self.TAGS[typ][labels.MAX_SPEED]
            # create edges
            current_node = None
            for node in road['nodes']:
                if current_node is not None:
                    graph.add_edge(current_node, node, **road)
                    if road.get('oneway', 'no') != 'yes':
                        graph.add_edge(node, current_node, **road)
                current_node = node
        return graph

    def get_graph(self, min_lon, min_lat, max_lon, max_lat):
        roads, nodes = self.call_api(min_lon, min_lat, max_lon, max_lat)
        graph = self.convert_into_graph(roads, nodes)
        return graph
