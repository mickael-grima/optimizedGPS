# -*- coding: utf-8 -*-
# !/bin/env python

from graphicInterface.GPSInterface import GPSInterface
import Tkinter

import logging
log = logging.getLogger(__name__)


class GUI(object):
    def __init__(self, graph, solver, width=0, length=0, **kwards):
        """ graph: problem input
            solver: how to solve the problem
        """
        self.root = Tkinter.Tk()
        self.interface = GPSInterface(self.root, self.getSimulator(graph, solver, **kwards), width=width, length=length)
        self.interface.pack()

    def getSimulator(self, graph, solver, **kwards):
        log.info("Solving problem %s ...", solver.__name__)
        prob = solver(graph, **kwards)
        prob.solve()
        log.info("Problem solved")
        return prob.getSimulator()

    def launchInterface(self):
        self.interface.mainloop()
        self.root.destroy()
