# -*- coding: utf-8 -*-
# !/bin/env python

import requests

from api import API
from optimizedGPS import options
from utils.files_manager import __get_data_from_file__, __write_data_to_file__
from utils.format_manager import __check_call_api_format__
from utils.geo_manager import generate_tile_column_row

__all__ = ["MapQuestTrafficAPI", "HereTrafficAPI", "TomtomTrafficAPI"]


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
    PROJECTION = "EPSG4326"

    @__check_call_api_format__
    @__get_data_from_file__
    @__write_data_to_file__
    def call_api(self, min_lon, min_lat, max_lon, max_lat, zoom="18"):
        box = "%s,%s,%s,%s" % (min_lon, min_lat, max_lon, max_lat)
        url = self.url.format(box=box, zoom=zoom)
        params = dict(
            key=self.key,
            projection=self.PROJECTION
        )

        resp = requests.get(url, params=params)
        resp = resp.json()
        resp["status"] = options.SUCCESS

        return resp
