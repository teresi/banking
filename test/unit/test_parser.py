#!/usr/bin/env python3

"""
Test ParserBase
"""

import logging
import tempfile
import coloredlogs
import datetime
import os
from contextlib import contextmanager

import pytest

from banking.parser import Parser
from banking.transaction import TransactionColumns, TransactionHistory
from banking.utils import file_dne_exc

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


FAKE_TRANSACTIONS="""date,type,check,note,amount
01/01/2020,Credit,,LEGIT EMPLOYER,$+1000
01/02/2020,Debit,,ESTABLISHMENT STORE DEBIT CARD,($42)
02/01/2020,Deposit,,TRANSFER FROM,$+3.50,
02/03/2020,POS,,ESTABLISHMENT DEBIT PURCHASE,($3.50)"""


class ParserImpl(Parser):
    """Implementation of a Parser for testing."""

    _MIN_DATE = datetime.date(1970, 1, 1)  # MAGIC arbirtrary

    VERSION = 1
    INSTITUTION = "Totally Legit Bank"
    DELIMETER = ","
    FIELD_NAMES = ["date", "amount", "note"]
    FIELD_2_TRANSACTION = {
        "date": TransactionColumns.DATE.name,
        "note": TransactionColumns.DESCRIPTION.name,
        "amount": TransactionColumns.AMOUNT.name,
    }

    ACCOUNT_NUMBER = 8888  # MAGIC fake acount
    FILE_PREFIX_PART = "Acct_"  # MAGIC fake file formatting
    FILE_PREFIX = FILE_PREFIX_PART + str(ACCOUNT_NUMBER)

    @classmethod
    def is_date_valid(cls, start, stop):
        """True if the dates found are valid for this parser."""

        return start >= cls._MIN_DATE

    def parse(self):
        """"""

        return TransactionHistory()

    @classmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser."""

        account_header = cls.FILE_PREFIX
        file_name = os.path.basename(filepath)
        matched = account_header in file_name
        if not matched:
            logging.debug("{} is invalid for {}".format(file_name, cls.__name__))
        return matched


@pytest.fixture
def temp_dir():
    """Temporary directory."""

    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():

    with tempfile.NamedTemporaryFile() as file:
        return file.name


@contextmanager
def temp_data(prefix=None, suffix=".csv", data=None):
    """Temporary file with data."""

    with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, mode='w+') as file:
        if data is not None:
            file.write(data)
        file.seek(0)
        yield file.name  # opening again by caller my not work in Windows?


@pytest.fixture
def temp_valid_input_file():

    with temp_data(
        prefix=ParserImpl.FILE_PREFIX,
        suffix='.csv',
        data=FAKE_TRANSACTIONS) as file_name:

        yield file_name


@pytest.fixture
def parser(temp_valid_input_file):

    parser = ParserImpl(temp_valid_input_file)
    yield parser


def test_subclass_is_registered(temp_file):
    """Does the sub class get registered?"""

    assert ParserImpl.__name__ in Parser.SUBCLASSES
    assert ParserImpl in Parser.SUBCLASSES.values()


def test_init_raise_file_no_exist():
    """Does init raise if file does not exist?"""

    with pytest.raises(FileNotFoundError):
        ParserImpl("/this/filepath/does/not/exist/really")


def test_check_header_read_file():
    """Is a good header accepted?"""

    data = ",".join(ParserImpl.FIELD_NAMES)
    with temp_data(prefix=ParserImpl.FILE_PREFIX, suffix=".csv", data=data) as file:
        assert ParserImpl.check_header(file, header=data, row=0) == True
        assert ParserImpl.is_file_parsable(file) == True


def test_is_parsable_bad_contents():
    """Is a file with bad header contents rejected?"""

    data = "this,is,the,wrong,header"
    with temp_data(prefix=None, suffix=".csv", data=data) as file:
        assert ParserImpl.check_header(file, row=0) == False
        assert ParserImpl.is_file_parsable(file) == False


def test_is_parsable_bad_filename():
    """Is a bad filename rejected?"""

    with temp_data(prefix="invalid_prefix") as file:
        assert ParserImpl.is_file_parsable(file) == False


def test_is_parsable_good_header():
    """Is a file with a good filename and header accepted?"""

    data = ",".join(ParserImpl.FIELD_NAMES)
    with temp_data(prefix=ParserImpl.FILE_PREFIX, suffix=".csv", data=data) as file:
        assert ParserImpl.is_file_parsable(file) == True


def test_parse_text_frame_rows(parser):
    """Does the frame read give the right number of transactions?"""

    # MAGIC our fake data has the first row as the header
    frame = parser.parse_textfile(header_index=0)
    # MAGIC -1 for the header
    n_transactions = len(FAKE_TRANSACTIONS.split('\n')) - 1
    rows, cols = frame.shape
    assert n_transactions == rows


def test_parse_text_frame_sum(parser):
    """Does reading the data give the right sum for debit / credit?"""

    sum = -1

    assert sum == 1000-42


if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
