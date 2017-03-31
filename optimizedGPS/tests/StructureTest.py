# -*- coding: utf-8 -*-
# !/bin/env python

import logging

from optimizedGPS.logger import configure

configure()
log = logging.getLogger(__name__)

import unittest
from networkx import NetworkXError
from optimizedGPS.structure import Graph
from optimizedGPS.structure import GPSGraph
from optimizedGPS.structure import TimeExpandedGraph
from optimizedGPS.data.data_generator import generate_graph_from_file
from optimizedGPS.structure import Driver


class StructureTest(unittest.TestCase):
    def setUp(self):
        log.info("STARTING tests")

    def testStructure(self):
        graph = Graph(name='graph')

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        # Nodes
        self.assertTrue(graph.has_node('node0'))
        self.assertFalse(graph.has_node('node2'))

        self.assertEqual({'node0', 'node1'}, set(graph.nodes()))

        # Edges
        self.assertTrue(graph.has_edge('node0', 'node1'''))
        self.assertFalse(graph.has_edge('node1', 'node2'))
        self.assertFalse(graph.has_edge('node1', 'node0'))  # is directed graph
        self.assertEqual({'distance': 100, 'lanes': 1, 'size': 3}, graph.get_edge_data('node0', 'node1'))
        self.assertIsNone(graph.get_edge_data('node1', 'node0'))
        self.assertEqual({'node0 --> node1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.edges())))
        self.assertEqual('node1', graph.successors_iter('node0').next())

        # remove
        self.assertRaises(NetworkXError, graph.remove_node, 'node2')
        graph.remove_node('node0')
        self.assertFalse(graph.has_node('node0'))
        self.assertFalse(graph.has_edge('node0', 'node1'))

    def testStats(self):
        graph = Graph(name='graph')

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        stats = graph.get_stats()
        st = {'nodes': 2, 'edges': 1, 'av_degree': 1.0, 'connected_components': 1, 'unique_sens': 1, 'double_sens': 0}

        self.assertEqual(stats, st)

    def testDrivers(self):
        graph = GPSGraph(name='graph')

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        driver0 = Driver('node0', 'node1', 0)
        driver1 = Driver('node0', 'node2', 2)
        driver2 = Driver('node0', 'node2', 2)

        # add drivers
        self.assertTrue(graph.add_driver(driver0))
        self.assertFalse(graph.add_driver(driver1))
        self.assertTrue(graph.add_driver(driver2, force=True))

        # "has" assertions
        self.assertTrue(graph.has_driver(driver0))
        self.assertFalse(graph.has_driver(driver1))
        self.assertTrue(graph.has_driver(driver2))

        # "getAll" functions
        self.assertEqual({driver0, driver2}, set(graph.get_all_drivers()))
        self.assertEqual({driver0, driver2}, set(graph.get_all_drivers_from_starting_node('node0')))
        self.assertEqual(driver0, graph.get_all_drivers_to_ending_node('node1').next())

        # properties
        self.assertTrue(graph.set_drivers_property(driver0, 'names', {'first': 'first', 'last': 'last'}))
        self.assertIsNone(graph.get_drivers_property(driver1, 'names'))
        self.assertEqual({'first': 'first', 'last': 'last'}, graph.get_drivers_property(driver0, 'names'))

        # remove
        self.assertTrue(graph.remove_driver(driver0))
        self.assertTrue(graph.has_driver(driver2))
        self.assertFalse(graph.has_driver(driver0))
        self.assertFalse(graph.remove_driver(driver0))

    def testParser(self):
        graph = generate_graph_from_file('static/graph-test-0.graphml')

        # Nodes
        self.assertTrue(graph.has_node('n0'))
        self.assertFalse(graph.has_node('n2'))

        self.assertEqual({'n0', 'n1'}, set(graph.nodes()))

        # Edges
        self.assertTrue(graph.has_edge('n0', 'n1'))
        self.assertFalse(graph.has_edge('n1', 'n0'))
        self.assertFalse(graph.has_edge('n1', 'n0'))  # is directed graph
        self.assertIsNone(graph.get_edge_data('n1', 'n0'))
        self.assertEqual({'n0 --> n1'}, set(map(lambda el: '%s --> %s' % (el[0], el[1]), graph.edges())))
        for source, target in graph.edges():
            self.assertTrue(graph.get_edge_property(source, target, "distance"))
            self.assertGreater(float(graph.get_edge_property(source, target, "distance")), 0.0)

        # data
        self.assertEqual(graph.get_position('n0'), (457.0, 296.0))

        # remove
        self.assertRaises(NetworkXError, graph.remove_node, 'n2')
        graph.remove_node('n0')
        self.assertFalse(graph.has_node('n0'))
        self.assertFalse(graph.has_edge('n0', 'n1'))

    def testDjikstra(self):
        graph = generate_graph_from_file('static/djikstra-test.graphml', distance_default=1.0)

        self.assertEqual(('1', '6', '7'), graph.get_paths_from_to('1', '7').next())
        self.assertEqual({('1', '6', '7'), ('1', '4', '5', '7')},
                         set(graph.get_paths_from_to('1', '7', length=1)))
        self.assertEqual({('1', '6', '7'), ('1', '4', '5', '7'), ('1', '4', '5', '6', '7'),
                              ('1', '4', '3', '5', '7'), ('1', '4', '3', '5', '6', '7'),
                              ('1', '2', '3', '5', '7'), ('1', '2', '3', '5', '6', '7'),
                              ('1', '6', '2', '3', '5', '7')},
                         set(graph.get_all_paths_without_cycle('1', '7')))

    def testGeneratePathFromEdges(self):
        graph = generate_graph_from_file('static/djikstra-test.graphml', distance_default=1.0)

        edges = [('2', '3'), ('1', '6'), ('5', '7'), ('3', '5'), ('6', '2')]
        path = graph.generate_path_from_edges('1', '7', edges)
        self.assertEqual(path, ('1', '6', '2', '3', '5', '7'))

        path = graph.generate_path_from_edges('1', '3', edges)
        self.assertEqual(path, ('1', '6', '2', '3'))

        self.assertRaises(Exception, graph.generate_path_from_edges, '1', '4', edges)

        edges = [('2', '3'), ('1', '6'), ('5', '7'), ('3', '5')]
        self.assertRaises(Exception, graph.generate_path_from_edges, '1', '7', edges)

    def testTimeExpandedGraphLinearCase(self):
        graph = Graph()
        graph.add_edge(1, 2)
        TEG = TimeExpandedGraph.create_time_expanded_graph_from_linear_congestion(graph, 3)
        self.assertEqual(TEG.nodes(), ['1:0', '1:1', '1:2', '2:2', '2:1', '2:0'])
        self.assertEqual(TEG.edges(), [('1:0', '2:2'), ('1:0', '2:1'), ('1:1', '2:2')])


if __name__ == '__main__':
    unittest.main()
