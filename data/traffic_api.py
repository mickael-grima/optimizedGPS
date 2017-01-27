# -*- coding: utf-8 -*-
# !/bin/env python

import requests
from api import API
from utils.files_manager import __get_data_from_file__, __write_data_to_file__
from utils.format_manager import __check_call_api_format__
from utils.geo_manager import generate_tile_column_row
import options
import math


class MapQuestTrafficAPI(API):
    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat, output_format="json"):
        params = dict(
            outFormat=output_format,
            boundingBox='%s,%s,%s,%s' % (max_lat, max_lon, min_lat, min_lon),
            key=self.key
        )
        resp = requests.get(self.url, params=params).json()
        resp["status"] = options.SUCCESS
        return resp


class HereTrafficAPI(API):
    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, lat, lon, zoom):
        params = dict(
            app_id=self.key["app_id"],
            app_code=self.key["app_code"],
        )
        xt, yt = generate_tile_column_row(lat, lon, zoom)

        resp = requests.get(self.url + "/%s/%s/%s" % (zoom, xt, yt), params=params).json()
        resp["status"] = options.SUCCESS
        return resp


class TomtomTrafficAPI(API):
    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat, zoom="11", projection="EPSG4326"):
        x_min, y_min = self.GEO.mercator_projection(min_lon, min_lat)
        x_max, y_max = self.GEO.mercator_projection(max_lon, max_lat)
        box = "%s,%s,%s,%s" % (y_min, x_min, y_max, y_min)
        url = self.url.format(box=box, zoom=zoom)
        params = dict(
            key=self.key,
            projection=projection
        )

        resp = requests.get(url, params=params)
        print resp.url
        resp = resp.json()
        resp["status"] = options.SUCCESS

        return resp
