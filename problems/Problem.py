# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.ModelTransformationSimulator import ModelTransformationSimulator
from gurobipy import GurobiError

import sys
import time
import gurobipy as gb
import logging
log = logging.getLogger(__name__)


class Problem(object):
    """ Initialize the problems' classes
    """
    def __init__(self, timeout=sys.maxint):
        self.value = 0  # final value of the problem
        self.running_time = 0  # running time
        self.opt_solution = {}  # On wich path are each driver
        self.timeout = timeout

        self.__timed_out = False

    def isTimedOut(self):
        return self.__timed_out

    def solve(self):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def addOptimalPathToDriver(self, driver, path):
        self.opt_solution.setdefault(driver, [])
        self.opt_solution[driver].append(path)

    def iterOptimalSolution(self):
        """ yield for each driver the path he had
        """
        for driver, paths in self.opt_solution.iteritems():
            for path in paths:
                yield driver, path

    def getGraph(self):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def getOptimalValue(self):
        paths = {}
        for driver, path in self.iterOptimalSolution():
            paths.setdefault(path, {})
            paths[path].setdefault(driver[2], 0)
            paths[path][driver[2]] += 1

        if not paths:
            log.warning("Problem has not been solved yet ! Problem=%s" % self.__class__.__name__)
            return 0.0
        simulator = ModelTransformationSimulator(self.getGraph(), paths)

        # simulate
        while simulator.has_next():
            simulator.next()

        return simulator.get_value()

    def getValue(self):
        return self.value

    def getRunningTime(self):
        return self.running_time


class SimulatorProblem(Problem):
    """ Initialize the simulator's model's classes
    """
    def __init__(self, timeout=sys.maxint):
        super(SimulatorProblem, self).__init__(timeout=timeout)

    def getGraph(self):
        return self.simulator.graph

    def setOptimalSolution(self):
        self.opt_solution = {}
        for driver, path in self.simulator.get_current_solution():
            self.addOptimalPathToDriver(driver, path)

    def simulate(self):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def solve(self):
        ct = time.time()

        # simulate
        self.simulate()

        self.running_time = time.time() - ct
        self.value = self.getOptimalValue()


class Model(Problem):
    """ Initialize the models' classes
    """
    def __init__(self, graph, timeout=sys.maxint, **params):
        super(Model, self).__init__(timeout=timeout)
        self.model = gb.Model()
        self.graph = graph
        params['TimeLimit'] = timeout
        params['LogToConsole'] = 0
        self.setParameters(**params)

        self.count = {}

        self.initialize(**params)
        self.buildModel()

    def initialize(self, *args, **kwards):
        pass

    def setParameters(self, **kwards):
        for key, value in kwards.iteritems():
            self.model.setParam(key, value)

    def buildConstants(self):
        pass

    def buildVariables(self):
        pass

    def addConstraint(self, constr, name=None):
        """ constr: constraint to add
            name: name of the constraint. For counting we split this name wrt ":".
            after ":" the words are here only to make the constraint unique inside Gurobipy
        """
        if name is None:
            name = 0
            while str(name) in self.count:
                name += 1

        name = str(name)
        self.count.setdefault(name.split(':')[0], 0)
        self.model.addConstr(constr, name)
        self.count[name.split(':')[0]] += 1

    def buildConstraints(self):
        pass

    def setObjective(self):
        pass

    def buildModel(self):
        log.info("** Model building STARTED **")
        self.buildConstants()
        self.buildVariables()
        self.model.update()
        self.buildConstraints()
        self.setObjective()
        log.info("** Model building FINISHED **")

    def optimize(self):
        self.model.optimize()

    def solve(self):
        t = time.time()
        self.optimize()
        self.running_time = time.time() - t
        self.setOptimalSolution()
        self.value = self.getOptimalValue()

    def getGraph(self):
        return self.graph

    def getObj(self):
        try:
            return self.model.ObjVal
        except GurobiError:
            log.warning("problem has not been solved yet")
            return sys.maxint
