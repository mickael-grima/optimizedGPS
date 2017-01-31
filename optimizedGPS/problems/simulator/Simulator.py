# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""
import logging

import matplotlib.pyplot as plt
import networkx as nx
import yaml

from utils.tools import assert_file_location

__all__ = []

log = logging.getLogger(__name__)


class Simulator(object):
    def __init__(self, graph):
        """
        Graph on which we run the simulation
        """
        self.graph = graph
        """
        Properties about the simulator
        """
        self._props = yaml.load(open('config.yml', 'r')).get('properties', {})

    def initialize(self):
        """
        we define here the dynamic class intances
        """
        """
        the previous computed states. They are sorted from the latest to the earliest one
        """
        self.previous_states = []
        """
        The time waited by the drivers. See Subclasses for how we compute it.
        """
        self.time = 0
        """
        Current clock of the simulation. The simulation has run `self.current_clock` units of time.
        """
        self.current_clock = 0

    def reinitialize(self, state={}):
        """
        return to the first step or to the given `state`

        :param state: state of the simulator. To know more about the structure, see :func:``get_current_state``
        """
        if state:
            for attr, value in state.iteritems():
                setattr(self, attr, value)
        else:
            self.initialize()

    def get_current_state(self):
        """
        save the dynamic classe's instances into a dictionary.
        This dictionary contains attribute's names as keys and associated attributes as values.

        ** WARNING **: Do not forget to copy the instances since it will be modified by next() method
        """
        return {'time': self.time}

    def has_previous_state(self):
        """
        Return True if the actual state is not the first one. More precisely returns True if there is at least one
        state saved in `self.previous_states`.

        :return: boolean
        """
        return len(self.previous_states) > 0

    def save_current_state(self):
        """
        Save the current state using method :func:``get_current_state``.
        """
        self.previous_states.append(self.get_current_state())

    def previous(self, state=None):
        """
        Reinitialize the simulator to his previous state.

        :param state: dictionary representing a state.
        """
        if state is not None:
            self.reinitialize(state=state)
        elif self.has_previous_state():
            self.reinitialize(state=self.previous_states[-1])
            del self.previous_states[-1]
        else:
            log.error("No previous state found")
            raise Exception("No previous state found")

    def has_next(self):
        """
        Check if there is a next step.
        """
        return False

    def next(self):
        """
        Compute the next step of the simulation.

        ** WARNING **: to be implemented
        """
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_value(self):
        """
        returns the value of the problem.

        :return: float
        """
        return self.time

    def get_current_solution(self):
        """
        Return the solution associated to the current state. It is generally a dictionary of driver, path where to each
        driver we associate a path.

        ** WARNING **: to be implemented
        """
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_traffics(self):
        """
        return the traffic on each edge.

        ** WARNING **: to be implemented
        """
        log.error("Not implemented yet")
        raise NotImplementedError()

    def get_color_from_traffic(self, edge, traffic):
        """
        Compute the color associated to the traffic. Considering the traffic limit of `edge` we compute the time_suppl,
        which is the deviation of `traffic` with traffic limit. Then regarding the properties, we return the
        corresponding color.

        :param edge: edge
        :param traffic: traffic on `edge`

        :return: string
        """
        cong_func = self.graph.get_congestion_function(*edge)
        time_suppl = (cong_func(traffic) - cong_func(0.0)) / cong_func(0.0)
        keys = sorted(self._props['traffics'].iterkeys(), reverse=True)
        for key in keys:
            if key <= time_suppl:
                return self._props['traffic-colors'][self._props['traffics'][key]]

    def to_image(self, fname=None, **kwargs):
        """
        Produce an image describing the current step and print it in a new matplotlib window.

        * options:

            * ``fname=None``: file name where the image is stored. if None we don't store the image.
            * ``**kwards``: additional properties for the :func:``networkx.draw <networkx.draw>`` function
        """
        traffics = self.get_traffics()
        for edge in self.graph.edges():
            self.graph.add_edge(*edge, traffic=traffics.get(edge, 0.0))

        colors = map(lambda e: self.get_color_from_traffic(e, traffics.get(e, 0.0)), self.graph.edges())
        positions = {}
        for n in self.graph.nodes():
            if self.graph.get_position(n) is not None:
                positions[n] = self.graph.get_position(n)
            else:
                positions = {}
                break

        nx.draw(self.graph, pos=positions, node_color='#000000', edge_color=colors, **kwargs)
        if fname is not None:
            assert_file_location(fname, typ='picture')
            plt.savefig(fname)
            plt.clf()
