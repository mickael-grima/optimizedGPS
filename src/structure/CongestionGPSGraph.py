# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from logger import configure

from structure.GPSGraph import GPSGraph
from structure.utils.tools import get_id

configure()
log = logging.getLogger(__name__)


class CongestionGPSGraph(GPSGraph):
    def __init__(self, name='graph'):
        super(CongestionGPSGraph, self).__init__(name=name)

    def getCongestionFunction(self, source, target):
        edge = self.getEdge(source, target)
        if edge is not None:
            return edge.getCongestionFunction()

    def getAllCongestionFunctions(self):
        res = {}
        for edge in self.getAllEdges():
            res.setdefault(get_id(edge.source), {})
            res[get_id(edge.source)].setdefault(get_id(edge.target),
                                                self.getCongestionFunction(edge.source, edge.target))
        return res
