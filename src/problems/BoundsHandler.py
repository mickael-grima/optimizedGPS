# -*- coding: utf-8 -*-
# !/bin/env python

from collections import namedtuple
import sys

import logging
log = logging.getLogger(__name__)

ALGO = namedtuple('algo', ['algo', 'args', 'kwards'])


class BoundsHandler(object):
    def __init__(self, graph):
        self.graph = graph
        self.lowers = []
        self.uppers = []

        # Best lower and upper bounds
        self.__interval = (- sys.maxint - 1, sys.maxint)

    def appendLowerBound(self, algorithm, *args, **kwards):
        self.lowers.append(ALGO(algorithm, args, kwards))

    def appendUpperBound(self, algorithm, *args, **kwards):
        self.uppers.append(ALGO(algorithm, args, kwards))

    def getLowerBound(self):
        return self.__interval[0]

    def getUpperBound(self):
        return self.__interval[1]

    def getInterval(self):
        return self.__interval

    def computeLowerBound(self):
        for algo in self.lowers:
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            try:
                a.solve()
                self.__interval = (max(self.getLowerBound(), a.getOptimalValue()), self.getUpperBound())
            except:
                log.warning("FAIL to solve Algorithm %s", algo.algo.__name__)

    def computeUpperBound(self):
        for algo in self.uppers:
            a = algo.algo(self.graph, *algo.args, **algo.kwards)
            try:
                a.solve()
                self.__interval = (self.getLowerBound(), min(a.getOptimalValue(), self.getUpperBound()))
            except:
                log.warning("FAIL to solve Algorithm %s", algo.algo.__name__)
