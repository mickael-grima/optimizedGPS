# -*- coding: utf-8 -*-
# !/bin/env python

import logging
import logging.config

import yaml

import options


def configure():
    with open("%s/config.yml" % options.PACKAGE_PATH, 'r') as ymlfile:
        logging.config.dictConfig(yaml.load(ymlfile)['logging'])
