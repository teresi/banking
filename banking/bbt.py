#!/usr/bin/env python3

"""
BBT / Truist transactions.
"""

import datetime
import csv

from banking.parser import Parser

# TODO parse dates
# TODO parse debit/credit
# TODO map categories to master categories (need regex for bbt)


class _Line(object):
    """One entry of the BBT transaction file."""

    @staticmethod
    def convert_nothing(field):
        return field

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

        if price.startswith('($'):  # negative
            number = price[2:-1]  # remove ($...)
            return -1 * float(number)
        elif price.startswith('$+'):  # positive
            number = price[2:]  # remove $+
            return +1 * float(number)
        else:
            msg = "can't parse price, doesn't start with '($' or '$+': {}".format(price)
            raise ValueError(msg)


class BbtParser(Parser):
    """Reads BBT transactions into a common format."""

    VERSION = 1
    _INSTITUTION = 'bbt'
    FILE_DELIMITER = ','
    FIELD_TYPES = [ ('Date', 'date', _Line.convert_date),
                    ('Check Number', 'check', int),
                    ('Description', 'category', _Line.convert_category),
                    ('Amount', 'price', _Line.convert_price) ]


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

        with open(self.history_filepath) as input_file:
            reader = csv.DictReader(input_file, delimiter=self.FILE_DELIMITER)
            
            for line in reader:
                fields = self._parse_line(line)

    def _parse_line(self, line):
        """Convert a line in text file to the transaction fields.

        Args:
            (iterable): the fields in raw string format.
        Returns:
            (dict): the entries defined in self.FIELD_TYPES
        """

        return
        fields = {}
        for idx, key, str2val in self.FIELD_TYPES:
            val = str2val(line[idx])
            fields[key] = val
        return fields

    def _filter_lines(self):
        """Remove lines."""
        pass

    def parse(self):

        raise NotImplementedError()















