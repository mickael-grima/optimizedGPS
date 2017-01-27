# -*- coding: utf-8 -*-
# !/bin/env python

import json
import options
import utils.geo_manager as geo


class API(object):
    FILES_FORMAT = "%s/data/files/{directory}/{name}.{output_format}" % options.PROJECT_PATH
    CONFIG_FILE = "%s/data/api_config.json" % options.PROJECT_PATH

    GEO = geo

    def __init__(self):
        with open(self.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        self.key = config['key'].get(self.__class__.__name__)
        self.url = config['url'].get(self.__class__.__name__)

    def call_api(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet")

    def get_file_name(self, *args, **kwargs):
        output_format = kwargs.get("output_format", "json")
        return self.FILES_FORMAT.format(
            directory=self.__class__.__name__,
            name="_".join(map(lambda e: str(e), args)),
            output_format=output_format
        )
