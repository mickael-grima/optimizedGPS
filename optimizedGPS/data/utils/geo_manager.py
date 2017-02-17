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


# degrees to radians
def degToRad(degrees):
    return math.pi * degrees / 180.0


# radians to degrees
def radToDeg(radians):
    return 180.0 * radians / math.pi

# Semi-axes of WGS-84 geoidal reference
WGS84_a = 6378137.0  # Major semiaxis [m]
WGS84_b = 6356752.3  # Minor semiaxis [m]


# Earth radius at a given latitude, according to the WGS-84 ellipsoid [m]
def WGS84EarthRadius(lat):
    # http://en.wikipedia.org/wiki/Earth_radius
    An = WGS84_a*WGS84_a * math.cos(lat)
    Bn = WGS84_b*WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt((An*An + Bn*Bn)/(Ad*Ad + Bd*Bd))

# Bounding box surrounding the point at given coordinates,
# assuming local approximation of Earth surface as a sphere
# of radius given by WGS84
def boundingBox(latitudeInDegrees, longitudeInDegrees, halfSideInKm):
    lat = degToRad(latitudeInDegrees)
    lon = degToRad(longitudeInDegrees)
    halfSide = 1000*halfSideInKm

    # Radius of Earth at given latitude
    radius = WGS84EarthRadius(lat)
    # Radius of the parallel at given latitude
    pradius = radius*math.cos(lat)

    latMin = lat - halfSide/radius
    latMax = lat + halfSide/radius
    lonMin = lon - halfSide/pradius
    lonMax = lon + halfSide/pradius

    return map(radToDeg, [latMin, lonMin, latMax, lonMax])
