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
        self.__congestionFunctions = {}  # We store here the congestions function for each edge

    def setCongestionFunction(self, source, target, func):
        if self.hasEdge(source, target):
            source_id, target_id = get_id(source), get_id(target)
            self.__congestionFunctions.setdefault(source_id, {})
            self.__congestionFunctions[source_id].setdefault(target_id, func)
            log.info("Congestion func added to edge (%s, %s)", source.name, target.name)
            return True
        return False

    def hasCongestionFunction(self, source, target):
        if (self.__congestionFunctions.get(get_id(source)) or {}).get(get_id(target)) is None:
            log.warning("There exists no congestion function on edge (%s, %s)", source.name, target.name)
            return False
        return True

    def getCongestionFunction(self, source, target):
        if self.hasCongestionFunction(source, target):
            return self.__congestionFunctions[get_id(source)][get_id(target)]
        return None

    def getAllCongestionFunctions(self):
        res = {}
        for source_id, dct in self.__congestionFunctions.iteritems():
            for target_id, func in dct.iteritems():
                source, target = self.getNodeById(source_id), self.getNodeById(target_id)
                res.setdefault((source.name, target.name), func)
        return res

    def removeCongestionFunction(self, source, target):
        if self.hasCongestionFunction(source, target):
            del self.__congestionFunctions[get_id(source)][get_id(target)]
            log.info("Congestion function on edge (%s, %s) removed", source.name, target.name)
            return True
        return False
