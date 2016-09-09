# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from logger import configure
from utils.tools import congestion_function

configure()
log = logging.getLogger(__name__)


class Edge(object):
    def __init__(self, source, target, **kwards):
        self.__dict__.update(kwards)

        self.__source = source
        self.__target = target

        self.__size = kwards.get('size', 0)
        self.__length = kwards.get('length', 0)

        self.__traffic = kwards.get('traffic', 0)

    @property
    def source(self):
        return self.__source

    @property
    def target(self):
        return self.__target

    @property
    def name(self):
        return '%s --> %s' % (self.source.name, self.target.name)

    @property
    def size(self):
        return self.__size

    @property
    def length(self):
        return self.__length

    @property
    def traffic(self):
        return self.__traffic

    def getCongestionFunction(self):
        return congestion_function(self.traffic, self.size, self.length)
