#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
A class for calling back after an asynchronous operation
"""

#
# Distributed under the terms of the MIT license.
#

import time, sys


class CallbackObject(object):
    """ Callback object """
    def __init__(self):
        pass

    def __call__(self, page, error, optReturn1 = None, optReturn2 = None):
        self.page = page
        self.error = error
        self.optReturn1 = optReturn1
        self.optReturn2 = optReturn2

