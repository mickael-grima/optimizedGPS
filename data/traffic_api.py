# -*- coding: utf-8 -*-
# !/bin/env python

import requests
from api import API
from utils.files_manager import __get_data_from_file__, __write_data_to_file__
from utils.format_manager import __check_call_api_format__
import options


class TrafficAPI(API):
    def __init__(self):
        super(TrafficAPI, self).__init__("https://www.mapquestapi.com/traffic/v2/incidents")

    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat, output_format="json", directory="mapquestapi"):
        params = dict(
            outFormat=output_format,
            boundingBox='%s,%s,%s,%s' % (min_lon, min_lat, max_lon, max_lat),
            key=self.key
        )
        resp = requests.get(self.url, params=params).json()
        resp["status"] = options.SUCCESS
        return resp
