# -*- coding: utf-8 -*-
# !/bin/env python

import json
import options


class API(object):
    FILES_FORMAT = "%s/data/files/{directory}/{name}.{output_format}" % options.PROJECT_PATH

    def __init__(self, url):
        with open("%s/data/api_keys.json" % options.PROJECT_PATH, 'r') as f:
            keys = json.load(f)
        self.key = keys.get(self.__class__.__name__)
        self.url = url

    def call_api(self, *args, **kwargs):
        raise NotImplementedError("Not implemented yet")

    def get_file_name(self, *args, **kwargs):
        output_format = kwargs.get("output_format", "json")
        return self.FILES_FORMAT.format(
            directory=self.__class__.__name__,
            name="_".join(map(lambda e: str(e), args)),
            output_format=output_format
        )
