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


    def __init__(self, filepath, parser):
        self._data = None  # TODO pd.dataframe init?
        # TODO: read file, parse, grab columns, check, add to internal _array
    
    def __add__(self, other):
        raise NotImplementedError

    def _remove_duplicates(self):
        raise NotImplementedError
        

class TransactionFactory(object):

    # TODO: build cls 2 parser map, find csv files, create history for each
    pass


class TransactioParser(object):
    """Base class for parsing the exported transaction histories (e.g. csv).

    Requires the csv filename format of:  <BANK>_<ACCOUNT>_<DATE_0>-<DATE_1>.<ext>
    """

    VERSION = None
    _INSTITUTION = None
    FILE_DELIMTER = ','  # csv, tab, etc.

    def __init__(self, csv_path):
        pass

    @property
    def INSTITUTION(self):
        return str.lower(str(self._INSTITUTION))

    @staticmethod
    def lines(filepath):
        """Yields lines from text file.
    
        Args:
            filepath (str): path to the text (serialized) transactions.
        Yields:
            (tuple): the fields.
        """

        with open(filepath) as ascii_file:
            reader = csv.reader(ascii_file, delimiter=',')
            for row in reader:
                yield row

    @classmethod
    def name2keys(cls, filepath):
        """Return various identifiers from the transaction history filename.

        Expects 3 '_' delimited fields.

        Returns:
            bank (str): the institution.
            account (str): the account ID.
            date (str): the transaction dates.
        """

        base = os.path.filename(str(filepath))
        filename, ext = os.path.splitext(base)
        fields = filename.split('_')
        try:
            bank, account, date = fields
        except ValueError as verr:
            msg = " expected 3 '_' delimited fields in filename; {}".format(str(verr))
            raise ValueError(msg)
        return bank, account, date

    @classmethod
    def parse_date(cls, date):
        """Parse a duration from the date field of the filename."""

        try:
            date0, date1 = date.split('-')
        except ValueError as verr:
            msg = " expected 2 '-' delimited fields in the date; {}".format(str(verr))
            raise ValueError(msg)

    @property
    def date(self):
        raise NotImplementedError

    @property
    def description(self):
        raise NotImplementedError

    @property
    def category(self):
        raise NotImplementedError

    @property
    def amount(self):
        raise NotImplementedError

