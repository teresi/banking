#!/usr/bin/env python3

"""
USAA transactions.
"""

import datetime

from banking.parser import Parser

# TODO parse dates
# TODO parse debit/credit
# TODO map categories to master categories (need regex for bbt)


class _Line(object):
    """One entry of the USAA transaction file."""

    @staticmethod
    def convert_nothing(field):
        return field

    @staticmethod
    def convert_posted(posted_field):
        return posted_field == 'posted'

    @staticmethod
    def convert_date(date_field):
        return datetime.datetime(str(date_field), "%M/%D/%Y")

    @staticmethod
    def convert_category(category):
        return category  # TODO add mapping

    @staticmethod
    def convert_price(price):

        if price.startswith('--'):
            return float(price[2:])
        elif price.startswith('-'):
            return float(price[1:])
        else:
            msg = "debit/credit doesn't start with '-' | '--': {}".format(price)
            raise ValueError(msg)


class UsaaParser(Parser):
    """Reads USAA transactions into a common format."""

    VERSION = 1
    _INSTITUTION = 'usaa'
    FILE_DELIMITER = ','
    FIELD_TYPES = [ (0, 'posted', _Line.convert_posted),
                    (2, 'date', _Line.convert_date),
                    (4, 'description', _Line.convert_nothing),
                    (5, 'category', _Line.convert_category),
                    (6, 'price', _Line.convert_price) ]

    def __init__(self, textfile_path):
        pass

    @classmethod
    def is_date_valid(cls, start, stop):
        """True if this parser should be used for the date provided.

        Args:
            start (datetime.datetime): begin date of transactions.
            stop (datetime.datetime): end date of transactions.
        """

        # MAGIC NUMBER currently only QA'd for 2019 and newer
        return start >= datetime.date(2019, 1, 1)

    def _parse_textfile(self, textfile_path):

        with open(textfile_path) as input_file:
            reader = csv.reader(input_file, delimiter=self.FILE_DELIMITER)
            for line in reader:
                fields = self._parse_line(line)


    def _parse_line(self, line):
        """Convert a line in text file to the transaction fields.

        Args:
            (iterable): the fields in raw string format.
        Returns:
            (dict): the entries defined in self.FIELD_TYPES
        """

        fields = {}
        for idx, key, str2val in self.FIELD_TYPES:
            val = str2val(line[idx])
            fields.update(key, val)
        return fields















