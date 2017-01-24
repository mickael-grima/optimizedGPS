# -*- coding: utf-8 -*-
# !/bin/env python

"""
    Here we find everything related to the osm api
"""

from osmapi import OsmApi, ApiError
from api import API
from utils.format_manager import __check_call_api_format__
from utils.files_manager import __get_data_from_file__, __write_data_to_file__

from optimizedGPS import labels
from optimizedGPS import options
from optimizedGPS.structure import GPSGraph

__all__ = ["RoadMapper"]


def is_node(el):
    return el.get('type') == 'node'


def get_tag(el):
    return el.get('data', {}).get('tag', {})


def get_node_location(node):
    return node.get('data', {}).get(labels.LATITUDE), node.get('data', {}).get(labels.LONGITUDE)


def get_node_id(node):
    return node.get('data', {}).get('id')


def iter_road_nodes(road):
    """
    Return the list of nodes' ids belonging to the road el

    :param road: a dictionary returned by OsmApi
    :return: iterator of nodes' ids
    """
    for idd in road.get('data', {}).get('nd', []):
        yield idd


class RoadMapper(API):
    ATTRIBUTES = {
        'highway': {
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
    }

    def __init__(self):
        self._api = OsmApi()

    def is_road(self, el):
        """
        Check if el is a road. el is a road iff it has a 'way' type and a 'highway' as key in its data

        :param el: a dictionnary returned by OsmApi
        :return: True if el is a road, else False
        """
        return el.get('type') == 'way' and 'highway' in get_tag(el) \
               and get_tag(el)['highway'] in self.ATTRIBUTES['highway']

    def is_oneway_road(self, el):
        return self.is_road(el) and get_tag(el).get('oneway', 'no') == 'yes'

    # TODO
    def is_in_agglomeration(self, road):
        """
        Return whether the road is in agglomeration

        :param road: dictionary representing a road
        :return: A boolean
        """
        return False

    def get_road_max_speed(self, road):
        """
        Read in the parameters or take the default value
        Return the max speed considering whether the road is in agglomeration

        :param road: dictionary representing a road
        :return: an integer
        """
        typ = get_tag(road)['highway']
        max_speed = get_tag(road).get(labels.MAX_SPEED) or self.ATTRIBUTES['highway'][typ][labels.MAX_SPEED]
        if isinstance(max_speed, str):
            if '|' in max_speed:
                if self.is_in_agglomeration(road):
                    return int(max_speed.split('|')[0])
                else:
                    return int(max_speed.split('|')[1])
            else:
                return int(max_speed)
        else:
            return max_speed

    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat):
        """
        We call the api to get the wanted data, and filter it to just keep roads and concerning nodes

        :param min_lon: see OsmApi.Map
        :param min_lat: see OsmApi.Map
        :param max_lon: see OsmApi.Map
        :param max_lat: see OsmApi.Map
        :return: A dictionary containing the ways and concerning node of the map
        """
        try:
            mapp = self._api.Map(min_lon, min_lat, max_lon, max_lat)
        except ApiError:
            mapp = {'status': options.FAILED}
            return mapp

        road_map = {'status': options.SUCCESS, 'roads': [], 'nodes': {}}
        # Find the roads first and save nodes' ids
        for el in mapp:
            if self.is_road(el):
                del el["data"]["timestamp"]
                road_map['roads'].append(el)
                for node in iter_road_nodes(el):
                    road_map['nodes'].setdefault(node, None)
        # Find the previous saved nodes' location
        for el in mapp:
            if is_node(el) and get_node_id(el) in road_map['nodes']:
                del el["data"]["timestamp"]
                road_map['nodes'][get_node_id(el)] = el

        return road_map

    def convert_into_graph(self, road_map):
        """
        Convert the map to a GPSGraph

        :param road_map: map gotten by getRoadMap method
        :return: a GPSGraph object
        """
        graph = GPSGraph()
        # First add the nodes
        for node in filter(lambda n: n is not None, road_map['nodes'].itervalues()):
            lat, lon = get_node_location(node)
            graph.add_node(get_node_id(node), lat, lon)
        # Then add the edges between nodes
        for road in road_map['roads']:
            typ = get_tag(road)['highway']
            props = {
                labels.LANES: get_tag(road).get(labels.LANES) or self.ATTRIBUTES['highway'][typ][labels.LANES],
                labels.MAX_SPEED: self.get_road_max_speed(road)
            }
            nodes = iter_road_nodes(road)
            current_node = None
            for node in nodes:
                if current_node is not None:
                    graph.add_edge(current_node, node, **props)
                    if not self.is_oneway_road(road):
                        graph.add_edge(node, current_node, **props)
                current_node = node
        return graph

    def get_graph(self, min_lon, min_lat, max_lon, max_lat):
        road_map = self.call_api(min_lon, min_lat, max_lon, max_lat)
        graph = self.convert_into_graph(road_map)
        return graph
