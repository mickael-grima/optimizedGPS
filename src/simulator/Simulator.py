# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""

import logging
log = logging.getLogger(__name__)


class Simulator(object):
    def __init__(self, graph):
        self.graph = graph

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

    def to_image(self):
        """ Produce an image describing the current step
        """
        log.error("Not implemented yet")
        raise NotImplementedError()
