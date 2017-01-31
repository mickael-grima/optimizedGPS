# -*- coding: utf-8 -*-
# !/bin/env python

import json
import datetime


def __check_call_api_format__(func):
    """
    Check whether the data returned by call_api has the right format
      - It should be a dictionary
      - In the dictionary we should have a key "status": This key tell us if we got the right data or not
      - The data should be json encodable
      - Add the date if it doesn't exist

    :param func: function
    :return:
    """
    def check_format(*args, **kwargs):
        data = func(*args, **kwargs)
        if not isinstance(data, dict):
            raise TypeError("Data should be a dict, got %s instead" % type(data))
        if "status" not in data:
            raise KeyError("Key 'status' should exist in data")
        data.setdefault("date", datetime.datetime.now().strftime("%H:%M:%S_%d-%m-%Y"))
        try:
            json.dumps(data)
        except:
            raise
        return data
    return check_format
