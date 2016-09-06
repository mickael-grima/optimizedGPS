# -*- coding: utf-8 -*-
# !/bin/env python

from GPSGraph import GPSGraph
from utils.tools import congestion_function
import logging

log = logging.getLogger(__name__)


class CongestionGPSGraph(GPSGraph):
    def __init__(self, name='graph'):
        super(CongestionGPSGraph, self).__init__(name=name)

    def getCongestionFunction(self, source, target):
        if self.hasEdge(source, target):
            return congestion_function(**self.getEdgeProperties(source, target))
