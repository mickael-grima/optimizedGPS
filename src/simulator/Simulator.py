# -*- coding: utf-8 -*-
"""
Created on Wed Apr 01 21:38:37 2015

@author: Mickael Grima
"""


class Simulator(object):
    def __init__(self):
        pass

    def next(self):
        """ Next step of the simulation
        """
        pass

    def previous(self):
        """ previous step in the simulation
        """
        pass

    def has_next(self):
        """ Check if there is a next step
        """
        return False

    def to_image(self):
        """ Produce an image describing the current step
        """
        raise NotImplementedError()

    def reinitialize(self):
        """ return to the first step
        """
        pass
