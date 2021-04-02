#!/usr/bin/env python3

"""
Interpret files to produce banking transactions.
"""


import datetime
import os
from collections import defaultdict
import logging
import errno

from abc import abstractmethod, abstractproperty

import pandas as pd

from banking.transaction import TransactionHistory
from banking.utils import file_dne_exc

# TODO add history class that wraps a numpy array (or dataframe) and defines the columns


class Parser:
    """Base class for parsing the exported transaction histories (e.g. csv)."""

    SUBCLASSES = {}

    def __init_subclass__(cls, **kwargs):
        """Register implementation."""

        super().__init_subclass__(**kwargs)
        cls.SUBCLASSES[cls.__name__] = cls

    def __init__(self, filepath, logger=None):
        """Initialize.

        Args:
            filepath(str): path to input data
            logger(logging.Logger): logger, create new if None
        """

        self.filepath = filepath
        self.logger = logger or logging.getLogger(__name__)

        if not os.path.isfile(self.filepath):
            raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), self.filepath)

    @abstractproperty
    def INSTITUTION(cls):
        """The name of the bank."""

        return str()

    @abstractproperty
    def FIELD_2_TRANSACTION(self):
        """Dict of subclass column names to TransactionHistory columns."""

        return {}

    @abstractproperty
    def FIELD_NAMES(self):
        """Column headers, unordered list of string names."""

        return []

    @abstractproperty
    def DELIMITER(self):
        """Data delimiter, e.g. ','"""

        return ","

    @abstractmethod
    def parse(self):
        """Return a TransactionHistory representation of the data."""

        return TransactionHistory()

    @classmethod
    def check_header(cls, filepath, header=None, row=0, delim=','):
        """True if all the expected field names are in the header.

        Args:
            filepath(str): path to input data file
            header(str): header contents, read file if None
            row(int): row index of the header line (zero based)
            delim(str): char delimiter
        Returns:
            (bool): true if header has all the expected fields
        """

        if header is None:
            line = [l for l in cls.yield_header(filepath, rows=row)][row]
        else:
            line = str(header).split(delim)

        matched = all([h in line for h in cls.FIELD_NAMES])
        return matched

    @classmethod
    def is_file_parsable(cls, filepath, header=None):
        """True if this parser can decode the input file.

        Tests the filepath and header.

        Args:
            filepath(str): path to input data
            header(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        if not cls._check_filename(filepath):
            return False

        return cls.check_header(filepath, header)

    @staticmethod
    def yield_header(filepath, rows=4, max_bytes_per_row=9000):
        """Yield rows from top of file.

        Args:
            filepath(str): path to the file
            rows(int): maximum rows to read
            max_bytes_per_row(int): cutoff line at bye count
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        with open(filepath, 'r') as handle:
            lines = handle.readlines(max_bytes_per_row)
            for i, line in enumerate(lines):
                yield line
                if i > rows:
                    break

    def parse_textfile(self, header_index=0, header_to_converter=None):
        """Read ASCII into pandas.

        Args:
            header_index(int): row index of header (column names),
            header_to_converter(dict(str: callable)): functions to convert row contents
        """

        frame = pd.read_csv(
            self.filepath,
            header=header_index,
            delimiter=self.DELIMITER,
            usecols=self.FIELD_NAMES,
            converters=header_to_converter,
        )
        return frame

