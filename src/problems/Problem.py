# -*- coding: utf-8 -*-
# !/bin/env python

from simulator.GPSSimulator import GPSSimulator
from utils.tools import isclose
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

    def setOptimalSolution(self, solution):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

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
        simulator = GPSSimulator(self.getGraph(), paths)

        # simulate
        while simulator.has_next():
            simulator.next()

        return simulator.get_value()


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

    def setParameters(self, NumericFocus=0, Presolve=-1, LogToConsole=0, TimeLimit=sys.maxint):
        self.model.setParam('NumericFocus', NumericFocus)
        self.model.setParam('Presolve', Presolve)
        self.model.setParam('TimeLimit', TimeLimit)
        self.model.setParam('LogToConsole', LogToConsole)

    def buildVariables(self):
        pass

    def buildConstraints(self):
        pass

    def setObjective(self):
        pass

    def buildModel(self):
        log.info("** Model building STARTED **")
        self.buildVariables()
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


class ColumnGenerationModel(Model):
    def __init__(self, graph, timeout=sys.maxint, **params):
        super(ColumnGenerationModel, self).__init__(graph, timeout=timeout, **params)
        self.values = []

    def addInstance(self, *index):
        pass

    def addVariable(self, *index):
        pass

    def addConstraint(self, *index):
        pass

    def generateNewColumn(self, *index):
        self.addInstance(*index)
        self.addVariable(*index)
        self.addConstraint(*index)

    def getBestGapConstraintIndex(self):
        """ find worst constraint and return the corresponding index
        """
        return (None,)

    def isComplete(self):
        """ True if no other variables can be added
        """
        return True

    def stopIteration(self):
        return self.isComplete() or (len(self.values) >= 2 and isclose(self.values[-1], self.values[-2]))

    def optimizeOneStep(self):
        super(ColumnGenerationModel, self).optimize()
        self.values.append(self.getObj())

    def optimize(self):
        """ TODO: among drivers who have still one path, choose the drivers which are implicated in
                  a high traffic edge, and among these drivers choose the worst one
        """
        while not self.stopIteration():
            self.optimizeOneStep()
            index = self.getBestGapConstraintIndex()
            if not all(index):
                break
            self.generateNewColumn(*index)
