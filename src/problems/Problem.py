# -*- coding: utf-8 -*-
# !/bin/env python

import sys
import logging
log = logging.getLogger(__name__)


class Problem(object):
    """ Initialize the problems' classes
    """
    def __init__(self, timeout=sys.maxint):
        self.value = 0
        self.running_time = 0
        self.opt_solution = None
        self.timeout = timeout

    def solve(self):
        log.error("Not implemented yet")
        raise NotImplementedError("Not implemented yet")

    def getOptimalSolution(self):
        return self.opt_solution
