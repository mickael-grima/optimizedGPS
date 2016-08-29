# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from logger import configure

configure()
log = logging.getLogger(__name__)


class Edge(object):
    def __init__(self, source, target, **kwards):
        for attr, value in kwards.iteritems():
            setattr(self, attr, value)
        self.__source = source
        self.__target = target

    @property
    def source(self):
        return self.__source

    @property
    def target(self):
        return self.__target

    @property
    def name(self):
        return '%s --> %s' % (self.source.name, self.target.name)
