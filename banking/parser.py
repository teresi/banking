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

from banking.utils import file_dne_exc, TransactionColumns


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

    @property
    @abstractmethod
    def INSTITUTION(cls):
        """The name of the bank."""

        return str()

    @property
    @abstractmethod
    def FIELD_2_TRANSACTION(self):
        """Dict of subclass column names to TransactionColumns names."""

        return {}

    @property
    @abstractmethod
    def FIELD_NAMES(self):
        """Column headers of the input file, unordered."""

        return []

    @property
    @abstractmethod
    def DELIMITER(self):
        """Column separator, e.g. ','"""

        return ","

    @property
    @abstractmethod
    def COL_2_CONVERTER(self):
        """Dictionary of functions to convert column values from input file.

        Returns: dict(str: callable(str))
        """

        return {}

    @abstractmethod
    def parse(self):
        """Return transactions as a panda frame with our column formatting.

        Returns:
            (pandas.DataFrame): frame with TransactionColumns column names
        """

        if not self.is_file_parsable(self.filepath):
            raise ValueError("cannot parse input file, invalid implementation {}:  {}"
                            .format(self.__class__.__name__, self.filepath))

        frame_raw = self.parse_textfile(header_to_converter=self.COL_2_CONVERTER)
        frame_mapped = self.remap_cols(frame_raw)
        return frame_mapped


    @classmethod
    @abstractmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser."""

        return False

    @classmethod
    def check_header(cls, filepath, header=None, row=0, delim=','):
        """True if all the expected field names are in the header.

        Used to select a parser for an input file based on the header contents.

        Args:
            filepath(str): path to input data file
            header(str): header contents, read file if None
            row(int): row index of the header line (zero based)
            delim(str): char delimiter
        Returns:
            (bool): true if header has all the expected fields
        """

        if row < 0:
            raise ValueError("row index of %i is < 0" % row)

        if header is None:
            line = [l for l in cls.yield_header(filepath, rows=row)][row]
        else:
            line = str(header).split(delim)

        matched = all([h in line for h in cls.FIELD_NAMES])
        return matched

    @classmethod
    def is_file_parsable(cls, filepath, header=None):
        """True if this parser can decode the input file.

        Used to select a parser for an input file based on the filepath and header.

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
            max_bytes_per_row(int): cutoff line at byte count
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
        Returns:
            pandas.DataFrame: the data
        """

        frame = pd.read_csv(
            self.filepath,
            header=header_index,
            delimiter=self.DELIMITER,
            usecols=self.FIELD_NAMES,
            converters=header_to_converter,
        )
        return frame

    @classmethod
    def remap_cols(cls, frame):
        """Rename the columns to our convention.

        Args:
            frame(pandas.DataFrame): the data
        Returns:
            pandas.DataFrame: remapped data
        """

        remapped = frame.rename(columns=cls.FIELD_2_TRANSACTION)
        expected = [n for n in TransactionColumns.names()]
        missing = [col for col in expected
                    if col not in remapped.columns]
        for col in missing:
            remapped[col] = None
        return remapped
