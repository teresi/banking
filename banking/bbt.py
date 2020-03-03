#!/usr/bin/env python3

"""
BBT / Truist transactions.
"""

import datetime
from decimal import Decimal
import csv
import logging

import numpy as np
import pandas as pd

from banking.parser import Parser
from banking.transaction import TransactionColumns

# TODO parse dates
# TODO parse debit/credit
# TODO map categories to master categories (need regex for bbt)


class _BbtConvert1(object):
    """One entry of the BBT transaction file."""

    @staticmethod
    def convert_posted(posted_field):
        return posted_field == 'posted'

    @staticmethod
    def convert_date(date_field):
        return datetime.datetime.strptime(str(date_field), "%M/%d/%y")

    @staticmethod
    def convert_category(category):
        return category  # TODO add mapping

    @staticmethod
    def convert_price(price):

        logging.getLogger().debug("testing logging in converter...")
        if price.startswith('($'):  # negative
            number = price[2:-1]  # remove ($...)
            return -1 * Decimal(number)
        elif price.startswith('$+'):  # positive
            number = price[2:]  # remove $+
            return +1 * Decimal(number)
        else:
            msg = "can't parse price, doesn't start with '($' or '$+': {}".format(price)
            logging.getLogger().error(msg)
            return None

    @staticmethod
    def convert_check(check_number):

        if not check_number:
            # BUG missing check no. sometimes get converted to NaN, and then real ones to floats (b/c a Nan is a float and it casts the ints)
            return None
        else:
            return np.uint32(check_number)


class BbtParser1(Parser):
    """Reads BBT transactions into a common format."""

    VERSION = 1
    INSTITUTION = 'bbt'
    DELIMITER = ','
    FIELD_NAMES = ['Date', 'Transaction Type', 'Check Number', 'Description', 'Amount']
    FIELD_CONVERTERS = {'Date': _BbtConvert1.convert_date,
                        'category': _BbtConvert1.convert_category,
                        'Amount':  _BbtConvert1.convert_price,
                        'Check Number': _BbtConvert1.convert_check
                        }
    FIELD_2_TRANSACTION = {'Date': TransactionColumns.DATE.name,
                           'Check Number': TransactionColumns.CHECK_NO.name,
                           'Description': TransactionColumns.DESCRIPTION.name,
                           'Amount': TransactionColumns.AMOUNT.name
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

        frame = pd.read_csv(self.history_filepath,
                            header=0,  # MAGIC NUMBER the first line has the names
                            delimiter=self.DELIMITER,
                            usecols=self.FIELD_NAMES,
                            converters=self.FIELD_CONVERTERS
                            )
        return frame

    def _transaction_history(self, frame):
        """Convert custom columns to TransactionHistory."""

        frame.rename(columns=self.FIELD_2_TRANSACTION, inplace=True)
        frame[TransactionColumns.CATEGORY.name] = None  # FUTURE populate categories
        return frame

    def parse(self):

        self.logger.info("parsing %s at  %s", self.INSTITUTION, self.history_filepath)
        frame = self._parse_textfile()
        frame = self._transaction_history(frame)
        # FUTURE add & map categories
        print(frame)

        return None
