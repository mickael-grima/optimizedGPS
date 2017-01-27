# -*- coding: utf-8 -*-
# !/bin/env python

import math


def generate_tile_column_row(lat, lon, zoom):
    # Convert lat, lon and zoom to column and row
    latrad = lat * math.pi / 180.
    n = math.pow(2, zoom)
    xTile = n * ((lon + 180) / 360)
    yTile = n * (1 - (math.log(math.tan(latrad) + 1 / math.cos(latrad)) / math.pi)) / 2

    return xTile, yTile


def mercator_projection(lon, lat, unit="degree"):
    if unit == "degree":
        lon = math.pi * lon / 180.
        lat = math.pi * lat / 180.
    x = lon
    y = math.log(math.tan(math.pi / 4. + lat / 2.))
    return x, y


def mercator_projection_inverse(x, y):
    lon = x
    lat = math.atan(math.sinh(y))
    return lon, lat
