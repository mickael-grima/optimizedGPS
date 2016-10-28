# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""
import matplotlib.pyplot as plt
import networkx as nx

import logging
import yaml
from utils.tools import assert_file_location
log = logging.getLogger(__name__)


class Simulator(object):
    def __init__(self, graph):
        self.graph = graph
        self._props = yaml.load(open('config.yml', 'r')).get('properties', {})

    def initialize(self):
        """ we define here the dynamic class intances
        """
        self.previous_states = []
        self.time = 0

    def reinitialize(self, state={}):
        """ return to the first step
        """
        if state is None:
            self.initialize()
            return True
        return False

    def get_current_state(self):
        """ save the dynamic classe's instances

            WARNING: Do not forget to copy the instances since it will be modified by next() method
        """
        return {'time': self.time}

    def has_previous_state(self):
        return len(self.previous_states) > 0

    def save_current_state(self):
        self.previous_states.append(self.get_current_state())

    def previous(self, state=None):
        if state is not None:
            self.reinitialize(state=state)
        elif self.has_previous_state():
            self.reinitialize(state=self.previous_states[-1])
            del self.previous_states[-1]
        else:
            log.error("No previous state found")
            raise Exception("No previous state found")

    def has_next(self):
        """ Check if there is a next step
        """
        return False

    def next(self):
        """ Next step of the simulation
        """
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_value(self):
        return self.time

    def get_current_solution(self):
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_traffics(self):
        """ return the traffic on each edge
        """
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_color_from_traffic(self, edge, traffic):
        cong_func = self.graph.getCongestionFunction(*edge)
        time_suppl = (cong_func(traffic) - cong_func(0.0)) / cong_func(0.0)
        keys = sorted(self._props['traffics'].iterkeys(), reverse=True)
        for key in keys:
            if key <= time_suppl:
                return self._props['traffic-colors'][self._props['traffics'][key]]

    def to_image(self, fname=None, **kwards):
        """ Produce an image describing the current step
        """
        G = nx.DiGraph()
        G.add_nodes_from(self.graph.getAllNodes())

        traffics = self.get_traffics()
        for edge in self.graph.getAllEdges():
            G.add_edge(*edge, traffic=traffics.get(edge, 0.0))

        colors = map(lambda e: self.get_color_from_traffic(e, traffics.get(e, 0.0)), G.edges())
        try:
            positions = {n: (self.graph.getData(n)['x'], self.graph.getData(n)['y'])
                         for n in self.graph.getAllNodes()}
        except:
            positions = None

        nx.draw(G, pos=positions, node_color='#000000', edge_color=colors, **kwards)
        if fname is not None:
            assert_file_location(fname, typ='picture')
            plt.savefig(fname)
            plt.clf()
