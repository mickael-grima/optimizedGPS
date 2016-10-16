# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import logging
log = logging.getLogger(__name__)


class Problem(object):
    """ Initialize the problems' classes
    """
    def __init__(self, name='', timeout=sys.maxint):
        self.value = 0
        self.running_time = 0
        self.opt_solution = None
        self.timeout = timeout
        self.name = name or self.__class__.__name__

    def solve(self):
        log.info("-------------- %s: Solving STARTED --------------" % self.name)

    def getOptimalSolution(self):
        return self.opt_solution
