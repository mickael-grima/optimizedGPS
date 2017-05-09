# -*- coding: utf-8 -*-
# !/bin/env python

import unittest

from networkx import NetworkXError
from optimizedGPS.structure import Graph
from optimizedGPS.structure import GPSGraph
from optimizedGPS.structure import TimeExpandedGraph, ReducedTimeExpandedGraph
from optimizedGPS.data.data_generator import generate_graph_from_file
from optimizedGPS.structure import Driver
from optimizedGPS.structure import DriversGraph
from optimizedGPS.structure import DriversStructure


class StructureTest(unittest.TestCase):
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
        drivers_graph = DriversGraph()

        graph.add_node('node0')
        graph.add_node('node1')
        graph.add_edge('node0', 'node1', size=3)

        driver0 = Driver('node0', 'node1', 0)
        driver1 = Driver('node0', 'node2', 2)
        driver2 = Driver('node0', 'node2', 2)

        # add drivers
        drivers_graph.add_driver(driver0)
        drivers_graph.add_driver(driver2)
        self.assertRaises(TypeError, drivers_graph.add_driver, '4')

        # "has" assertions
        self.assertTrue(drivers_graph.has_driver(driver0))
        self.assertFalse(drivers_graph.has_driver(driver1))
        self.assertTrue(drivers_graph.has_driver(driver2))

        # "getAll" functions
        self.assertEqual({driver0, driver2}, set(drivers_graph.get_all_drivers()))
        self.assertEqual({driver0, driver2}, set(drivers_graph.get_all_drivers_from_starting_node('node0')))
        self.assertEqual(driver0, drivers_graph.get_all_drivers_to_ending_node('node1').next())

        # properties
        drivers_graph.add_driver(driver1, names=dict(first='first', last='last'))
        self.assertEqual({'first': 'first', 'last': 'last'}, drivers_graph.get_driver_property(driver1, 'names'))

        # remove
        drivers_graph.remove_driver(driver0)
        self.assertFalse(drivers_graph.has_driver(driver0))

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

    def testReducedTimeExpandedGraph(self):
        graph = Graph()
        graph.add_edge(1, 2)
        TEG = ReducedTimeExpandedGraph(graph, 2)
        self.assertEqual(set(TEG.nodes_iter()), {'1:::0', '1:::1', '1:::2', '2:::2', '2:::1', '2:::0'})
        self.assertEqual(set(TEG.edges_iter()), {('1:::0', '2:::2'), ('1:::0', '2:::1'), ('1:::1', '2:::2')})

    def testDriversStructure(self):
        graph = Graph()
        graph.add_edge(1, 2)
        graph.add_edge(1, 3)
        graph.add_edge(2, 3)

        drivers_graph = DriversGraph()
        driver1 = Driver(1, 2, 0)
        driver2 = Driver(1, 3, 0)
        drivers_graph.add_driver(driver1)
        drivers_graph.add_driver(driver2)

        drivers_structure = DriversStructure(graph, drivers_graph, horizon=10)
        # driver1
        drivers_structure.set_safety_interval_to_driver(driver1, (1, 2), (0, 5))
        drivers_structure.set_presence_interval_to_driver(driver1, (1, 2), (2, 3))
        drivers_structure.set_safety_interval_to_driver(driver1, (2, 3), (4, 7))
        drivers_structure.set_presence_interval_to_driver(driver1, (2, 3), (5, 7))
        drivers_structure.set_unreachable_edge_to_driver(driver1, (1, 3))
        # driver2
        drivers_structure.set_safety_interval_to_driver(driver2, (1, 2), (0, 3))
        drivers_structure.set_presence_interval_to_driver(driver2, (1, 2), (1, 3))
        drivers_structure.set_safety_interval_to_driver(driver2, (2, 3), (4, 17))
        drivers_structure.set_presence_interval_to_driver(driver2, (2, 3), (4, 7))
        drivers_structure.set_safety_interval_to_driver(driver2, (1, 3), (0, 5))
        drivers_structure.set_presence_interval_to_driver(driver2, (1, 3), (2, 3))

        # Set intervals
        self.assertRaises(Exception, drivers_structure.set_safety_interval_to_driver, driver1, (2, 3), (None, 3))
        self.assertRaises(Exception, drivers_structure.set_presence_interval_to_driver, driver2, (2, 3), (1, "rt"))

        # Reachable edges
        self.assertTrue(drivers_structure.is_edge_reachable_by_driver(driver1, (1, 2)))
        self.assertTrue(drivers_structure.is_edge_reachable_by_driver(driver2, (2, 3)))
        self.assertFalse(drivers_structure.is_edge_reachable_by_driver(driver1, (1, 3)))

        # get intervals
        self.assertEqual((0, 5), drivers_structure.get_safety_interval(driver2, (1, 3)))
        self.assertEqual((4, 10), drivers_structure.get_safety_interval(driver2, (2, 3)))
        self.assertEqual((0, 10), drivers_structure.get_largest_safety_interval_before_end(driver2))
        self.assertEqual((0, 5), drivers_structure.get_largest_safety_interval_after_start(driver2))

        # edges
        self.assertTrue(drivers_structure.are_edges_time_connected_for_driver(driver1, (1, 2), (2, 3)))
        self.assertFalse(drivers_structure.are_edges_time_connected_for_driver(driver2, (1, 2), (2, 3)))
        self.assertEqual(((1, 2), (1, 3)), tuple(drivers_structure.get_possible_edges_for_driver(driver2)))
        self.assertEqual(((1, 2), (2, 3)), tuple(drivers_structure.get_possible_edges_for_driver(driver1)))
        self.assertTrue(drivers_structure.are_drivers_dependent(driver1, driver2))


if __name__ == '__main__':
    unittest.main()
