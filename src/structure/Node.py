# -*- coding: utf-8 -*-
# !/bin/env python

import logging
from logger import configure

configure()
log = logging.getLogger(__name__)


class Node(object):
    def __init__(self, name='', **kwards):
        for attr, value in kwards.iteritems():
            setattr(self, attr, value)
        self.__name = name

    @property
    def name(self):
        return self.__name
