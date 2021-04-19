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

import numpy as np
import pandas as pd
from decimal import Decimal

from banking.parser import Parser
from banking.utils import TransactionColumns, TransactionCategories


_pos_price_pattern = re.compile("^--")
_neg_price_pattern = re.compile("^-")


def _convert_price(price):
    """Dollar to Decimal."""

    # TODO replace substrint call w/ word boundaries?
    # TODO catch Decimal exceptions / reject bad formats
    if _pos_price_pattern.search(price) is not None:
        return Decimal(price[2:])
    elif _neg_price_pattern.search(price) is not None:
        print(price[1:])
        return -1 * Decimal(price[1:])
    else:
        logging.error("cannot convert price:  %s" % price)
        return None


def _convert_date(date_field):
    """String to date."""

    return datetime.datetime.strptime(str(date_field), "%m/%d/%Y").date()


def _convert_posted(posted_field):
        return posted_field == "posted"


def _convert_category(category_field):

    return category_field  # TODO


class Usaa(Parser):
    """Reads USAA transactions into a common format."""

    INSTITUTION = "usaa"
    DELIMITER = ","

    # MAGIC NUMBER per usaa format
    FIELD_COLS = [0, 2, 4, 5, 6]
    FIELD_NAMES = ["posted", "date", "description", "category", "amount"]
    FIELD_CONVERTERS = {
        "posted": _convert_posted,
        "date": _convert_date,
        "category": _convert_category,
        "amount": _convert_price,
    }
    # MAGIC NUMBER map to TransacationHistory columns
    FIELD_2_TRANSACTION = {
        "date": TransactionColumns.DATE.name,
        "amount": TransactionColumns.AMOUNT.name,
        "description": TransactionColumns.DESCRIPTION.name,
        "category": TransactionColumns.CATEGORY.name,
    }

    @classmethod
    def is_date_valid(cls, start, stop):
        """True if this parser should be used for the date provided.

        Args:
            start (datetime.datetime): begin date of transactions.
            stop (datetime.datetime): end date of transactions.
        """

        # MAGIC NUMBER currently only QA'd for 2019 and newer
        return start >= datetime.date(2019, 1, 1)

    def _parse_textfile(self):
        """Read file into a data frame."""

        frame = pd.read_csv(
            self.history_filepath,
            header=None,  # MAGIC NUMBER file has no header line
            delimiter=self.DELIMITER,
            usecols=self.FIELD_COLS,
            names=self.FIELD_NAMES,
            converters=self.FIELD_CONVERTERS,
        )
        # remove incomplete transactions
        frame.drop(frame[frame.posted == False].index, inplace=True)

        return frame

    def _transaction_history(self, frame):
        """Convert custom columns to TransactionHistory."""

        # frame[TransactionColumns.BANK.name] = self.INSTITUTION
        # frame[TransactionColumns.ACCOUNT.name] = None  # NOTE reconsider this feature
        frame.rename(columns=self.FIELD_2_TRANSACTION, inplace=True)
        frame[TransactionColumns.CHECK_NO.name] = None
        return frame

    def parse(self):

        self.logger.info("parsing %s at  %s", self.INSTITUTION, self.history_filepath)
        frame = self._parse_textfile()
        frame = self._transaction_history(frame)
        # FUTURE refine & map categories
        print(frame)

        return None
