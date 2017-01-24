# -*- coding: utf-8 -*-
# !/bin/env python

import json
import os


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
