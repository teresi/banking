#!/usr/bin/env python3

"""
Stores transaction histories, e.g. credit / debit.
"""

from enum import Enum, unique, auto
import os
import logging
import datetime

import numpy as np
import pandas as pd


@unique
class TransactionColumns(Enum):
    """The names for the columns present in a TransactionHistory data frame."""

    DATE = auto()
    AMOUNT = auto()
    DESCRIPTION = auto()
    CATEGORY = auto()
    # BANK = auto()
    CHECK_NO = auto()
    # ACCOUNT = auto()


class TransactionHistory(object):
    """Wraps a data frame containing banking transactions."""

    VERSION = 1
    COLUMNS = [t.name for t in TransactionColumns]

    def __init__(self, data_frame=None):
        self.history = data_frame or pd.DataFrame([], columns=self.COLUMNS)

    @classmethod
    def from_dataframe(cls, data_frame):
        pass

    @classmethod
    def from_parsers(cls, parser_list):
        pass
