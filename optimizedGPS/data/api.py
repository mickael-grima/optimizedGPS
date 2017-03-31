# -*- coding: utf-8 -*-
# !/bin/env python

"""
Base class for every api
"""

import json

import utils.files_manager as fil
import utils.geo_manager as geo
from utils.exceptions import NonExistingData


class API(object):
    """
    Base class. Every othe api class should inherit from this class
    """

    """
    Path where files are stored
    """
    FILES_FORMAT = "data/files/{directory}/{name}.{output_format}"
    """
    Configuration concerning the api
    """
    CONFIG_FILE = "data/api_config.json"

    """
    Helper about geography data and computation
    """
    GEO = geo

    def __init__(self):
        with open(self.CONFIG_FILE, 'r') as f:
            config = json.load(f)
        """
        Key needed for calling the api
        """
        self.key = config['key'].get(self.__class__.__name__)
        """
        api's url
        """
        self.url = config['url'].get(self.__class__.__name__)

    def call_api(self, *args, **kwargs):
        """
        Main class for calling the api, should be implemented in each subclass
        """
        raise NotImplementedError("Not implemented yet")

    def get_file_name(self, *args, **kwargs):
        """
        Return the file's name considering the following argument
          - the folder is the name of the class
          - the name is built with args elements
          - if `output_format` is given in kwargs, we add it as format, else .json will be added

        :param args:
        :param kwargs:
        :return:
        """
        output_format = kwargs.get("output_format", "json")
        return self.FILES_FORMAT.format(
            directory=self.__class__.__name__,
            name="_".join(map(lambda e: str(e), args)),
            output_format=output_format
        )

    @classmethod
    def get_box(cls, city_name, country_code, area_size):
        """
        Considering a city name, country_code and an area_size we return the corresponding minimum and maximum
        latitude and longitude. The obtained bounded box corresponds then to the given city in the given country, and
        its size is exactly are_size

        :param city_name: City's name, as string
        :param country_code: country_code, as string
        :param area_size: float
        :return: tuple
        """
        countries = list(fil.iterate_supported_countries())
        if not country_code in countries:
            raise NonExistingData("No data for country_code=%s" % str(country_code))
        try:
            city = fil.iterate_city_by_name(country_code, city_name).next()
            lon, lat = float(city['lon']), float(city['lat'])
        except StopIteration:
            raise NonExistingData("City %s not supported for country=%s" % (city_name, country_code))
        return geo.boundingBox(lat, lon, area_size / 2.)
