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

# TODO parse dates
# TODO parse debit/credit
# TODO map categories to master categories (need regex for bbt)


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


class Bbt(Parser):
    """Reads BBT transactions into a common format."""

    INSTITUTION = "bbt"
    FIELD_2_TRANSACTION = {
        "Date": TransactionColumns.DATE.name,
        "Check Number": TransactionColumns.CHECK_NO.name,
        "Description": TransactionColumns.DESCRIPTION.name,
        "Amount": TransactionColumns.AMOUNT.name,
    }
    FIELD_NAMES = ["Date", "Transaction Type", "Check Number", "Description", "Amount"]
    DELIMITER = ","
    COL_2_CONVERTER = {
        "Date": _convert_date,
        "category": _convert_category,
        "Amount": _convert_price,
        "Check Number": _convert_check,
    }
    ACCOUNT = 7389

    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        return super().parse()

    @classmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser."""

        file_name = os.path.basename(filepath)
        prefix = "Acct_" + str(cls.ACCOUNT)
        return filepath.startswith(prefix)

