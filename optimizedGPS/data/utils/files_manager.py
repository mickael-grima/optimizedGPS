# -*- coding: utf-8 -*-
# !/bin/env python

import json
import os
import gzip

from exceptions import NonExistingData


DATA_PATH = os.path.dirname(os.path.realpath(__file__))
FILES_PATH = os.path.abspath(os.path.join(DATA_PATH, "..", "files"))


def exists_data(file_name):
    return os.path.exists(file_name)


def read_from_file(file_name, format="json"):
    with open(file_name, "r") as f:
        if format == "json":
            return json.load(f)
        return '\n'.join(f.readlines())


def ensure_dir(file_name):
    d = os.path.dirname(file_name)
    if not os.path.exists(d):
        os.makedirs(d)


def write_to_file(file_name, text):
    ensure_dir(file_name)
    with open(file_name, "w") as f:
        f.write(text)


def __get_data_from_file__(func):
    def get_data(*args, **kwargs):
        self = args[0]
        file_name = self.get_file_name(*args[1:], **kwargs)
        if exists_data(file_name):
            data = read_from_file(file_name)
            return data
        return func(*args, **kwargs)
    return get_data


def __write_data_to_file__(func):
    def write_data(*args, **kwargs):
        self = args[0]
        data = func(*args, **kwargs)
        file_name = self.get_file_name(*args[1:], **kwargs)
        write_to_file(file_name, json.dumps(data))
        return data
    return write_data


def iterate_supported_countries():
    path = os.path.join(FILES_PATH, "cities")
    for country in os.listdir(path):
        if os.path.isdir(os.path.join(path, country)):
            yield country


def iterate_main_cities(country):
    path = os.path.join(FILES_PATH, "cities", country, "main_cities.json.gz")
    if not os.path.exists(path):
        raise NonExistingData("Main cities not found for country=%s" % country)
    with gzip.open(path, "r") as f:
        for city in json.load(f):
            yield city


def iterate_main_cities_name(country):
    for city in iterate_main_cities(country):
        yield city["city"]


def iterate_cities(country):
    path = os.path.join(FILES_PATH, "cities", country, "cities.json.gz")
    if not os.path.exists(path):
        raise NonExistingData("Cities not found for country=%s" % country)
    with gzip.open(path, "r") as f:
        for city in json.load(f):
            yield city


def iterate_cities_name(country):
    for city in iterate_cities(country):
        yield city["city"]


def iterate_city_by_name(country, *city_names):
    for city in iterate_cities(country):
        if city["city"] in city_names:
            yield city
