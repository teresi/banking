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

    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        frame = super().parse()
        frame = self._fill_categories(frame)
        frame = frame.astype({
            TransactionColumns.CHECK_NO.name: np.int16
        })
        return frame

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

    def _fill_categories(self, frame):
        """Fill category entries given the description values."""

        # FUTURE is there a vectorized form of this in pandas?
        desc_name = TransactionColumns.DESCRIPTION.name
        frame[TransactionColumns.CATEGORY.name] = frame[desc_name].apply(_convert_category)
        return frame
