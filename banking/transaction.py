#!/usr/bin/env python3

"""
Stores transaction histories, e.g. credit / debit.
"""

import os
import logging
import datetime

import numpy as np
import pandas as pd

class TransactionHistory(object):

    VERSION = 1
    COLUMNS = ['DATE', 'AMOUNT', 'DESCRIPTION', 'CATEGORY', 'BANK', 'ACCOUNT', 'CHECK_NO']

    def __init__(self, data_frame=None):
        self.data_frame = data_frame or pd.DataFrame([], columns=self.COLUMNS)

    @classmethod
    def from_dataframe(cls, data_frame):
        pass

    @classmethod
    def from_parsers(cls, parser_list):
        pass


