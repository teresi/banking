#!/usr/bin/env python3

"""
USAA transactions.
"""

import datetime
import csv

import numpy as np
import pandas as pd
from decimal import Decimal

from banking.parser import Parser
from banking.transaction import TransactionColumns

# TODO parse dates
# TODO parse debit/credit
# TODO map categories to master categories (need regex for bbt)


class _UsaaConvert1(object):
    """Sundry functions to convert entries of the USAA transaction file."""

    @staticmethod
    def convert_posted(posted_field):
        return posted_field == 'posted'

    @staticmethod
    def convert_date(date_field):
        # NOTE the hour field is populated when pandas gets this data
        # what effect will that have?
        date_time = datetime.datetime.strptime(str(date_field), "%M/%d/%Y")
        return np.datetime64(date_time)

    @staticmethod
    def convert_category(category):
        return category  # TODO add mapping

    @staticmethod
    def convert_price(price):

        if price.startswith('--'):
            return Decimal(price[2:])
        elif price.startswith('-'):
            return Decimal(price[1:])
        else:
            return Decimal(price)  # used when price is forcasted

class UsaaParser1(Parser):
    """Reads USAA transactions into a common format."""

    VERSION = 1
    INSTITUTION = 'usaa'
    DELIMITER = ','

    # MAGIC NUMBER per usaa format
    FIELD_COLS = [0, 2, 4, 5, 6]
    FIELD_NAMES = ['posted', 'date', 'description', 'category', 'amount']
    FIELD_CONVERTERS = {'posted': _UsaaConvert1.convert_posted,
                        'date': _UsaaConvert1.convert_date,
                        'category': _UsaaConvert1.convert_category,
                        'amount':  _UsaaConvert1.convert_price
                        }
    # MAGIC NUMBER map to TransacationHistory columns
    FIELD_2_TRANSACTION = {'date': TransactionColumns.DATE.name,
                           'price': TransactionColumns.AMOUNT.name,
                           'description': TransactionColumns.DESCRIPTION.name,
                           'category': TransactionColumns.CATEGORY.name
                           }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
                            header=None,  # MAGIC NUMBER file has no header line
                            delimiter=self.DELIMITER,
                            usecols=self.FIELD_COLS,
                            names=self.FIELD_NAMES,
                            converters=self.FIELD_CONVERTERS
                           )
        # remove incomplete transactions
        frame.drop(frame[frame.posted==False].index, inplace=True)

        print(frame)
        return frame
    
    def parse(self):

        frame = self._parse_textfile()

        return None
