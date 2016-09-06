# -*- coding: utf-8 -*-
# !/bin/env python


class MissingKeysError(StandardError):
    """ One or more keys are missing """
    pass


class StructureError(StandardError):
    """ object structure error """
    pass


class WrongDataError(StandardError):
    """ the given data shouldn't be here """
    pass
