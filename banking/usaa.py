#!/usr/bin/env python3

"""
USAA transactions.
"""

import datetime
import csv
import re
import logging
from decimal import Decimal
from datetime import date
import os

import numpy as np
import pandas as pd
from decimal import Decimal

from banking.parser import Parser
from banking.utils import TransactionColumns, TransactionCategories
from banking.transactions import Transactions


_pos_price_pattern = re.compile(r"^\d+")
_neg_price_pattern = re.compile(r"^-\d+")


def _convert_price(price):
    """Dollar to Decimal."""

    # TODO replace substrint call w/ word boundaries?
    # TODO catch Decimal exceptions / reject bad formats
    if _pos_price_pattern.search(price) is not None:
        return Decimal(price)
    elif _neg_price_pattern.search(price) is not None:
        return -1 * Decimal(price[1:])
    else:
        logging.error("cannot convert price:  %s" % price)
        return None


def _convert_date(date_field):
    """String to date."""

    return datetime.datetime.strptime(str(date_field), "%m/%d/%Y").date()


def _convert_posted(posted_field):
    """Posted or focasted."""

    return posted_field == "posted"


def _convert_category(category_field):
    """Description to user category."""

    return category_field  # TODO


class Usaa(Parser):
    """Reads USAA transactions into a common format."""

    INSTITUTION = "usaa"
    DELIMITER = ","

    _DATE_COL_NAME = "date"  # MAGIC our convention, should match FIELD_NAME_TO_INDEX
    _AMOUNT_COL_NAME = "amount"  # MAGIC our convention, should match FIELD_NAME_TO_INDEX
    FIELD_NAME_TO_INDEX = {  # MAGIC column indices according to USAA
        "posted": 0,
        "date": 2,
        "description": 4,
        "category": 5,
        "amount": 6,
    }
    FIELD_CONVERTERS = {
        "posted": _convert_posted,
        "date": _convert_date,
        "category": _convert_category,
        "amount": _convert_price,
    }
    # MAGIC NUMBER map to TransacationHistory columns
    _FIELD_2_TRANSACTION = {
        "date": TransactionColumns.DATE.name,
        "amount": TransactionColumns.AMOUNT.name,
        "description": TransactionColumns.DESCRIPTION.name,
        "category": TransactionColumns.CATEGORY.name,
    }
    ACCOUNT = 9999

    @classmethod
    def field_2_transaction(cls):
        """Input column name to our standard column names."""

        return cls._FIELD_2_TRANSACTION

    def parse(self):
        """Return the cleaned data.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        if not self.is_file_parsable(self.filepath):
            raise ValueError("cannot parse input file, invalid implementation {}:  {}"
                            .format(self.__class__.__name__, self.filepath))

        frame = self._parse_textfile()
        frame = self._remove_unconfirmed_transactions(frame)
        frame = self._remap_column_names(frame)
        return Transactions(self.filepath, frame=frame)

    @staticmethod
    def _remove_unconfirmed_transactions(frame):
        """Remove transactions that haven't cleared."""

        frame.drop(frame[frame.posted == False].index, inplace=True)
        return frame

    def _parse_textfile(self):
        """Read file into a data frame."""

        field_names = list(self.FIELD_NAMES_TO_COLS.keys())
        field_indices = list(self.FIELD_NAMES_TO_COLS.values())
        frame = pd.read_csv(
            self.history_filepath,
            header=None,  # MAGIC file has no header line
            delimiter=self.DELIMITER,
            usecols=field_indices,
            names=field_indices,
            converters=self.FIELD_CONVERTERS,
        )
        return frame

    def _remap_column_names(self, frame):
        """Convert custom columns to TransactionHistory."""

        # frame[TransactionColumns.BANK.name] = self.INSTITUTION
        # frame[TransactionColumns.ACCOUNT.name] = None  # NOTE reconsider this feature
        frame.rename(columns=self._FIELD_2_TRANSACTION, inplace=True)
        frame[TransactionColumns.CHECK_NO.name] = None
        return frame

    @classmethod
    def is_file_parsable(cls, filepath, beginning=None):
        """True if this parser can decode the input file.

        Args:
            filepath(str): path to input data
            beginning(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        """

        super().is_file_parsable(filepath)

        # MAGIC USAA doesn't use a header and the first line will do
        lines = [l for l in cls.yield_header(filepath, rows=1)]
        try:
            first_line = lines[0]
        except IndexError:
            logging.error("file line count is 0:  %s" % filepath)
            return False

        # NOTE b/c USAA does not use a header, check a few properties of the data
        return all([
            cls.check_column_count(first_line), 
            cls.check_date_column(first_line),
            cls.check_amount_column(first_line),
        ])

    @classmethod
    def check_column_count(cls, line):
        """True if the input file has the right column count."""

        # MAGIC n_cols = n_delim + 1 (no trailing delimiter)
        cols = line.count(cls.DELIMITER) + 1
        expected = 7  # MAGIC USAA convention, not all are populated though
        logging.debug("col count %i cvs %i" % (cols, expected))
        return cols == expected

    @classmethod
    def check_date_column(cls, line):
        """True if the date was parsed succesfully."""

        try:
            date_val = cls.get_field(line, cls._DATE_COL_NAME)
        except (ValueError, IndexError, KeyError) as exc:
            return False
        else:
            return date_val is not None

    @classmethod
    def check_amount_column(cls, line):
        """True if the amount was parsed succesfully."""

        try:
            price_val = cls.get_field(line, cls._AMOUNT_COL_NAME)
        except (ValueError, IndexError, KeyError):
            return False
        return price_val is not None

    @classmethod
    def get_field(cls, line, column_name):
        """Extract parsed field from a line of the input file.

        Raises:
            KeyError: invalid column name
            IndexError: index for column missing in line
            ValueError: date not parsed correctly
        """

        # FUTURE this might be useful for other Parser implementations
        # refactor to generic solution?
        fields = line.split(cls.DELIMITER)
        index = cls.FIELD_NAME_TO_INDEX[column_name]
        try:
            field = fields[index]
            converter = cls.FIELD_CONVERTERS[column_name]
        except IndexError as i_err:
            logging.error("can't parse line for %s, index is missing: %s"
                          % (column_name, i_err))
            raise i_err
        except KeyError as k_err:
            logging.error("can't parse line for %s, converter is missing: %s"
                          % (column_name, k_err))
            raise k_err
        return converter(field)

