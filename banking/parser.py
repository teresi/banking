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
import numpy as np

from banking.utils import file_dne_exc, TransactionColumns
from banking.transactions import Transactions


class Parser:
    """Base class Factory to produce banking transacations in pandas.DataFrame format.

    Implement the functions to check and convert the input data.
    Call `is_file_parsable` to check if this parser is valid for the input file.
    Call `parse` to produce the frame.
    """

    _SUBCLASSES = {}

    def __init_subclass__(cls, **kwargs):
        """Register implementation."""

        super().__init_subclass__(**kwargs)
        cls._SUBCLASSES[cls.__name__] = cls

    @classmethod
    def gen_implementations(cls):
        """Generator of name, class for each subclass.

        Returns:
            generator(str, class): the items
        """

        return (cls._SUBCLASSES.items())

    def __init__(self, filepath, logger=None):
        """Initialize.

        Args:
            filepath(str): path to input data
            logger(logging.Logger): logger, create new if None
        """

        if not os.path.isfile(filepath):
            raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), filepath)

        self.logger = logger or logging.getLogger(__name__)
        self.filepath = filepath
        self.account = self.parse_account_number(self.filepath)

    @property
    @abstractmethod
    def INSTITUTION(cls):
        """The name of the bank."""

        return str()

    @classmethod
    @abstractmethod
    def field_2_transaction(cls):
        """Dict of subclass column names to TransactionColumns names."""

        return {}

    @classmethod
    def field_names(cls):
        """Column headers of the input file, unordered."""

        return [key for key in cls.field_2_transaction().keys()]

    @property
    @abstractmethod
    def DELIMITER(self):
        """Column separator, e.g. ','"""

        return ","

    @property
    @abstractmethod
    def COL_2_CONVERTER(self):
        """Dictionary of functions to convert column values from input file.

        Returns:
            dict(str: callable(str))
        """

        return {}

    @classmethod
    @abstractmethod
    def parse_account_number(csl, filepath):
        """Find the account number for the input file.

        Returns:
            (int): the account, typically last four digits of the account
        """

        return -1

    @abstractmethod
    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        Raises:
            ValueError: input data is malformed.  NOTE should this be a RuntimeError?
        """

        if not self.is_file_parsable(self.filepath):
            raise ValueError("cannot parse input file, invalid implementation {}:  {}"
                            .format(self.__class__.__name__, self.filepath))

        frame_raw = self.parse_textfile(header_to_converter=self.COL_2_CONVERTER)
        frame_mapped = self.remap_cols(frame_raw)
        return Transactions(self.filepath, frame=frame_mapped)

    @classmethod
    @abstractmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser."""

        return False

    @classmethod
    @abstractmethod
    def is_file_parsable(cls, filepath, beginning=None):
        """True if this parser can decode the input file.

        Used to select a parser for an input file based on the filepath and header.

        Args:
            filepath(str): path to input data
            beginning(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        Returns:
            (bool): true if it can be parsed by this class
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        return True

    @staticmethod
    def yield_header(filepath, rows=4, max_bytes_per_row=9000):
        """Yield rows from top of file.

        Args:
            filepath(str): path to the file
            rows(int): maximum rows to read
            max_bytes_per_row(int): cutoff line at byte count
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        # FUTURE this reads as utf-8; it might need to read as bytes here
        # and delay decoding, so as to not assume the file encoding here
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
        Returns:
            pandas.DataFrame: the data
        """

        frame = pd.read_csv(
            self.filepath,
            header=header_index,
            delimiter=self.DELIMITER,
            usecols=self.field_names(),
            converters=header_to_converter,
            dtype={TransactionColumns.CHECK_NO.name: np.int16}
        )
        frame[TransactionColumns.BANK.name] = self.INSTITUTION
        frame[TransactionColumns.ACCOUNT.name] = self.account
        return frame

    @classmethod
    def remap_cols(cls, frame):
        """Rename the columns to our convention.

        Args:
            frame(pandas.DataFrame): the data
        Returns:
            pandas.DataFrame: remapped data
        """

        remapped = frame.rename(columns=cls.field_2_transaction())
        expected = [n for n in TransactionColumns.names()]
        missing = [col for col in expected
                    if col not in remapped.columns]
        for col in missing:
            remapped[col] = None
        return remapped
