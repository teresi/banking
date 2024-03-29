#!/usr/bin/env python3

"""
BBT / Truist transactions.
"""

import datetime
from decimal import Decimal
import csv
import logging
import os
import re

import numpy as np
import pandas as pd

from banking.parser import Parser
from banking.utils import TransactionColumns
from banking.utils import TransactionCategories as Cats
from banking.transactions import Transactions

# TODO need class level logger, root logger too confusing
_pos_price_pattern = re.compile(r"^\(\$")
_neg_price_pattern = re.compile(r"^\$\+")


def _convert_price(price):
    """Dollar to Decimal:$(X) for negatives, $+X for positives."""

    # TODO replace substrint call w/ word boundaries?
    if _pos_price_pattern.search(price) is not None:
        number = price[2:-1]  # remove ($...)
        return -1 * Decimal(number)
    elif _neg_price_pattern.search(price) is not None:
        number = price[2:]  # remove $+
        return Decimal(number)
    else:
        msg = "can't parse price, doesn't start with '($' or '$+': {}".format(price)
        logging.getLogger().error(msg)
        return None


def _convert_date(date_field):
    """Parse time into date, form of 01/31/1970"""

    return datetime.datetime.strptime(str(date_field), "%m/%d/%Y").date()


def _convert_category(description):
    """Parse description from bank to user category e.g. Exxon --> gas."""

    # FUTURE implement real solution, this is just proof of concept
    # maybe something like this?
    # mask = df.keyword.str.contains('+', regex=False)
    # df.loc[~mask, 'keyword'] = "[" + df.loc[~mask, 'keyword'] + "]"

    cat_out = Cats.UNKNOWN
    if description is None:
        return cat_out

    desc = str(description).lower()
    if "salary" in desc:
        cat_out = Cats.SALARY
    elif "verizon" in desc:
        cat_out = Cats.COMMUNICATIONS
    elif "moneyline fid" in desc:
        cat_out = Cats.INVESTMENTS
    elif "kroger" in desc or "giant" in desc:
        cat_out = Cats.GROCERIES
    elif "va dmv" in desc:
        cat_out = Cats.TAXES
    elif "dental" in desc or "walgreens" in desc:
        cat_out = Cats.MEDICAL

    return cat_out.name


def _convert_check(check_number):
    """Parse number for the check, if used."""

    if check_number == '':
        return -1
    if check_number is None:
        return -1
    try:
        return np.int16(check_number)
    except ValueError as verr:  # e.g. empty string
        logging.error("could not parse check number '%s':  %s"
                      .format(check_number, verr))
        return -1


def _convert_posted_balance(balance):
    """Parse the daily posted balance, a sparse account balance."""

    if not balance:
        return None

    if balance.startswith("$"):
        number = balance[1:]  # remove ($...)
        return Decimal(number)
    else:
        msg = "can't parse posted balance, doesn't start with '$': {}".format(balance)
        logging.getLogger().error(msg)
        return None


# TODO convert class methods to instance for better debugging?
# need to know what the file is for better debug calls
# also it would be useful to know why a particular file can't be parsed
class Bbt(Parser):
    """Reads BBT transactions into a common format."""

    INSTITUTION = "bbt"  # MAGIC our convention
    _FIELD_2_TRANSACTION = {
        "Date": TransactionColumns.DATE.name,
        "Check Number": TransactionColumns.CHECK_NO.name,
        "Description": TransactionColumns.DESCRIPTION.name,
        "Amount": TransactionColumns.AMOUNT.name,
        "Daily Posted Balance": TransactionColumns.POSTED_BALANCE.name,
    }
    DELIMITER = ","
    COL_2_CONVERTER = {
        "Date": _convert_date,
        "Check Number": _convert_check,
        "Amount": _convert_price,
        "Daily Posted Balance": _convert_posted_balance
    }
    # MAGIC bbt has files of Acct_1234_01_31_2020_to_02_28_2020
    _FILENAME_PATTERN = re.compile(r"^([aA]cct_)([0-9]{4})_")
    FILE_PREFIX = "Acct_"   # MAGIC bbt convention for their files

    @classmethod
    def field_2_transaction(cls):
        """Input column name to our standard column names."""

        return cls._FIELD_2_TRANSACTION

    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        frame = super().parse().frame
        frame = self._fill_categories(frame)
        frame = frame.astype({
            TransactionColumns.CHECK_NO.name: np.int16
        })
        return Transactions(self.filepath, frame=frame)

    @classmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser.

        Args:
            str(filepath): path or filename for the input data file (e.g. csv)
        Returns:
            bool: true if the filename matches one this parser should use
        """

        file_name = os.path.basename(filepath)
        match = cls._FILENAME_PATTERN.search(file_name)
        return match is not None

    @classmethod
    def parse_account_number(cls, filepath):
        """Last 4 digits of account number given the input filepath.

        Args:
            str(filepath): path or filename for the input data file (e.g. csv)
        Returns:
            str: account number
            bool: true if the filename matches one this parser should use
        """

        file_name = os.path.basename(filepath)
        match = cls._FILENAME_PATTERN.search(file_name)
        fields = None if not match else match.groups()
        if not fields:
            return None
        account = None if len(fields) < 2 else fields[1]
        return int(account)

    def _fill_categories(self, frame):
        """Fill category entries given the description values."""

        # FUTURE is there a vectorized form of this in pandas?
        desc_name = TransactionColumns.DESCRIPTION.name
        frame[TransactionColumns.CATEGORY.name] = frame[desc_name].apply(_convert_category)
        return frame

    @classmethod
    def check_header(cls, filepath, header=None, row=0, delim=','):
        """True if all the expected field names are in the header.

        Used to select a parser for an input file based on the header contents.

        Args:
            filepath(str): path to input data file
            header(str): header line, read file if None
            row(int): row index of the header line (zero based)
            delim(str): char delimiter
        Returns:
            (bool): true if header has all the expected fields
        """

        if row < 0:
            raise ValueError("row index of %i is < 0" % row)

        if header is None:
            line = [l for l in cls.yield_header(filepath, rows=row)][row]
        else:
            line = str(header).split(delim)

        # BUG multiline header not handled!
        matched = all([h in line for h in cls.field_names()])
        return matched

    @classmethod
    def is_file_parsable(cls, filepath, beginning=None):
        """True if this parser can decode the input file.

        Used to select a parser for an input file based on the filepath and header.

        Args:
            filepath(str): path to input data
            beginning(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        if not cls._check_filename(filepath):
            logging.debug("%s cannot parse b/c filename mismatch: %s" % (cls.__name__, filepath))
            return False

        # BUG splitting multiple lines not tested & no input arg for header row!
        if beginning is not None:
            beginning = beginning.split('\n')[0]

        is_parsable = cls.check_header(filepath, beginning)

        logging.debug("can %s parse this file? %s, %s" %
                      (cls.__name__, "true" if is_parsable else "false", filepath))
        return is_parsable
