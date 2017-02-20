# -*- coding: utf-8 -*-
# !/bin/env python

import json

import utils.files_manager as fil
import utils.geo_manager as geo
from utils.exceptions import NonExistingData


class API(object):
    FILES_FORMAT = "data/files/{directory}/{name}.{output_format}"
    CONFIG_FILE = "data/api_config.json"

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

    @classmethod
    def get_box(cls, city_name, country_code, area_size):
        countries = list(fil.iterate_supported_countries())
        if not country_code in countries:
            raise NonExistingData("No data for country_code=%s" % str(country_code))
        try:
            city = fil.iterate_city_by_name(country_code, city_name).next()
            lon, lat = float(city['lon']), float(city['lat'])
        except StopIteration:
            raise NonExistingData("City %s not supported for country=%s" % (city_name, country_code))
        return geo.boundingBox(lat, lon, area_size / 2.)
