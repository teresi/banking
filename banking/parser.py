#!/usr/bin/env python3

"""
Used to parse files and produce banking transaction data.

Implement Parser to read the files, use ParserFactory to automate crawling the disk.
"""


import datetime
import os
from collections import defaultdict
import logging
import errno

from abc import ABCMeta, abstractmethod, abstractproperty

from banking.transaction import TransactionHistory
from banking.utils import file_dne_exc

# TODO add history class that wraps a numpy array (or dataframe) and defines the columns

class ParserFactory(object):
    """Creates Parser objects given ASCII files.

    Looks up available Parsers in the local registery to match the filename to Parser.
    """

    def __init__(self, logger=None):
        """Initializer."""

        self._logger = logger or logging.getLogger(__name__)
        self.institution_to_parsers = self._map_parsers()

        for bank, parser_list in self.institution_to_parsers.items():
            self._logger.debug(" '{}' has {} parsers".format(bank, len(parser_list)))

    def from_file(self, filepath):
        """Parser from filepath."""

        self._logger.debug("from_file:  {}".format(filepath))
        bank, account, date0, date1 = self._name_to_keys(filepath)
        parsers = self.institution_to_parsers[str.lower(bank)]
        parser = self._filter_parsers(parsers, date0, date1)
        if not parser:
            self._logger.warning("no valid parser for:  {}".format(filepath))
            return None
        return parser(filepath)

    def from_directory(self, root):
        """Yield parsers for a directory."""

        self._logger.info("reading history from {}".format(root))
        paths_ = (p for p in os.scandir(root) if os.path.isfile(p))
        paths = (p.path for p in paths_)  # posix.DirEntry --> str
        parsers = (self.from_file(p) for p in paths)

        return (p for p in parsers if p)  # remove None entries

    def parser_names(self):
        """Return map of institution to Parser class names; for debugging.

        Returns:
            dict(str, list(str)):  the institution map to parser class names.
        """

        institution_to_parser_names = defaultdict(list)
        for bank, parser_list in self.institution_to_parsers.items():
            institution_to_parser_names[bank].append([p.__name__ for p in parser_list])
        return institution_to_parser_names

    @staticmethod
    def parse_date(date):
        """Parse a duration from the date field of the filename.

        Expects '<date_0>-<date_1>'.
        """

        try:
            date0, date1 = date.split("-")
        except ValueError as verr:
            msg = " expected 2 '-' delimited fields in the date; {}".format(str(verr))
            raise ValueError(msg)

        return date0, date1

    @classmethod
    def _map_parsers(cls):
        """Dict of name of bank to iterable of Parsers.

        Requires caller to import all relevant Parser sub classes prior to invoking.
        """

        parser_dict = defaultdict(list)
        for parser_name, parser_class in _registry.items():
            if parser_class.INSTITUTION == str.lower(str(None)):
                continue
            parser_dict[parser_class.INSTITUTION].append(parser_class)
        return parser_dict

    @classmethod
    def _name_to_keys(cls, filepath):
        """Return various identifiers from the transaction history filename.

        Expects '<bank>_<account>_<date_0>-<date_1>.<ext>'.
        """

        file_base = os.path.basename(filepath)
        file_name, ext = os.path.splitext(file_base)
        bank, account, date = cls._parse_path(file_name)
        date0, date1 = Parser.parse_date(date)

        return bank, account, date0, date1

    @staticmethod
    def _parse_path(filepath):
        """Return various identifiers from the transaction history filename.

        Expects '<bank>_<account>_<date>.<ext>'.
        """

        base = os.path.basename(str(filepath))
        filename, ext = os.path.splitext(base)
        fields = filename.split("_")
        try:
            bank, account, date = fields
        except ValueError as verr:
            msg = " expected bank, account, date '_' delimited fields in filename; {}".format(
                filepath
            )
            raise ValueError(msg)

        return bank, account, date

    def _filter_parsers(self, parsers, date0, date1):
        """Filter the parser iterable for the time frame."""

        valid_parsers = [p for p in parsers if p.is_date_valid(date0, date1)]
        if len(valid_parsers) > 1:
            msg = "more than one parser exists for {} between {}...{}".format(
                institution, date0, date1
            )
            logger.error(msg)
            msg = "these parsers overlap in time and are ambiguous: {}".format(
                valid_parsers
            )
            logger.info(msg)
            return None
        return valid_parsers[0] if valid_parsers else None


class Parser:
    """Base class for parsing the exported transaction histories (e.g. csv).

    Requires the csv filename format of:  <BANK>_<ACCOUNT>_<DATE>.<ext>
    The 'DATE' field can be: <YYYYMM> OR <YYYYMM>-<YYYYMM>; one month OR start-stop.
    """

    SUBCLASSES = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.SUBCLASSES[cls.__name__] = cls

    def __init__(self, filepath, logger=None):

        self.filepath = filepath
        self.logger = logger or logging.getLogger(__name__)

        if not os.path.isfile(self.filepath):
            raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self.filepath)

    @abstractproperty
    def VERSION(cls):  # TODO remove?
        """Version of the parser."""

        return int()

    @abstractproperty
    def INSTITUTION(cls):
        """The name of the bank."""

        return str()

    @abstractproperty
    def FIELD_2_TRANSACTION(self):
        """Dict of subclass column names to TransactionHistory columns."""

        return {}

    @staticmethod
    def yield_header(filepath, rows=4, max_bytes_per_row=9000):
        """Yield rows from top of file.

        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        with open(filepath, 'r') as handle:
            lines = handle.readlines(max_bytes_per_row)
            for i, line in enumerate(lines):
                print(line)
                yield line
                if i > rows:
                    break


    @abstractmethod
    def is_date_valid(self, start, stop):
        """True if this parser should be used for the date provided.

        Args:
            start (datetime.datetime): begin date of transactions.
            stop (datetime.datetime): end date of transactions.
        """

        return False

    @abstractmethod
    def parse(self):
        """Return a TransactionHistory representation of the data."""

        return TransactionHistory()

    @staticmethod
    def _last_day_of_month(day):
        """The last day of the month from the date provided."""

        next_month = day.replace(day=28) + datetime.timedelta(days=4)
        return next_month - datetime.timedelta(days=next_month.day)

    @classmethod
    def parse_date(cls, date_str):
        """Convert the date to start / stop times.

        If stop is empty, uses last day of the month from start.

        Args:
            date_str(str): the date, YYYYMM or YYYYMM-YYYYMM, start & start-stop.

        Returns:
            (datetime.datetime): start date.
            (datetime.datetime): stop date.
        """

        if "-" in date_str:
            d0, d1 = date_str.split("-")
            start = cls._parse_date(d0)
            stop = cls._parse_date(d1)
        else:
            start = cls._parse_date(date_str)
            stop = cls._last_day_of_month(start)

        return start, stop

    @classmethod
    def _parse_date(cls, date):
        """Convert the expected date sub-string to datetime."""

        format = ""
        if len(date) == 6:
            format = "%Y%M"  # YYYYMM
        elif len(date) == 8:
            format = "%Y%M%d"  # YYYYMMDD
        else:
            raise ValueError("date is not YYYYMM or YYYYMMDD:  {}".format(date))

        time = datetime.datetime.strptime(date, format)
        return time.date()

    # TODO add is_valid_file to find if the input file works for this parser
    # remove the factory stuff that has the filename parsing etc.
    @classmethod
    @abstractmethod
    def is_file_parsable(cls, filepath, header=None):
        """True if this parser can decode the input file.

        Args:
            filepath(str): path to input data
            header(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        """


if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="read banking transactions")
    parser.add_argument("dir", type=str, help="dir of dir of banking transaction files")

    args = parser.parse_args()
