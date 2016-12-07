# -*- coding: utf-8 -*-
# !/bin/env python

import os
import logging
import logging.config
import yaml

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))


def configure():
    with open("%s/config.yml" % PROJECT_PATH, 'r') as ymlfile:
        logging.config.dictConfig(yaml.load(ymlfile)['logging'])
