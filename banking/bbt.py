#!/usr/bin/env python3

"""
BBT / Truist transactions.
"""

import datetime
from decimal import Decimal
import csv
import logging
import os

import numpy as np
import pandas as pd

from banking.parser import Parser
from banking.utils import TransactionColumns
from banking.utils import TransactionCategories as Cats


def _convert_price(price):
    """Dollar to Decimal:$(X) for negatives, $+X for positives."""

    if price.startswith("($"):  # negative
        number = price[2:-1]  # remove ($...)
        return -1 * Decimal(number)
    elif price.startswith("$+"):  # positive
        number = price[2:]  # remove $+
        return +1 * Decimal(number)
    else:
        msg = "can't parse price, doesn't start with '($' or '$+': {}".format(price)
        logging.getLogger().error(msg)
        return None


def _convert_date(date_field):
    """Parse time into date, form of 01/31/1970"""

    date = datetime.datetime.strptime(str(date_field), "%m/%d/%Y").date()
    return date


def _convert_category(category):
    """Parse category from bank to user category e.g. Exxon --> gas."""

    # FUTURE implement real solution, this is just proof of concept
    cat = category.lower()

    if "salary" in cat:
        return Cats.SALARY
    return category  # TODO add mapping


def _convert_check(check_number):
    """Parse number for the check, if used."""

    # NOTE have observed NaN / floats in some cases?
    if not check_number:
        return None

    try:
        return np.uint16(check_number)
    except ValueError:  # e.g. empty string
        return None


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
    ACCOUNT = 9999          # MAGIC last four digits of bbt account number
    FILE_PREFIX = "Acct_"   # MAGIC bbt convention for their files

    @classmethod
    def field_2_transaction(cls):
        """Input column name to our standard column names."""

        return cls._FIELD_2_TRANSACTION

    @classmethod
    def field_names(cls):
        """Columns expected in header, unordered."""

        return [key for key in cls._FIELD_2_TRANSACTION.keys()]

    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        return super().parse()

    @classmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser.

        Args:
            str(filepath): path or filename for the input data file (e.g. csv)
        Returns:
            bool: true if the filename matches one this parser should use
        """

        file_name = os.path.basename(filepath)
        # MAGIC bbt convention to have 'Acct_XXXX' as prefix
        prefix = "Acct_" + str(cls.ACCOUNT)
        return file_name.startswith(prefix)

