#!/usr/bin/env python3

"""
Test ParserBase
"""

import logging
import tempfile
import coloredlogs
import datetime
import os

import pytest

from banking.parser import Parser
from banking.transaction import TransactionColumns, TransactionHistory
from banking.utils import file_dne_exc

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


FAKE_ACCT="8888"
FAKE_TRANSACTIONS="""Date,Transaction Type,Check Number,Description,Amount,Daily Posted Balance
01/01/2020,Credit,,LEGIT EMPLOYER,$+1000,$0.00
01/02/2020,Debit,,ESTABLISHMENT STORE DEBIT CARD,($42),$958
02/01/2020,Deposit,,TRANSFER FROM,$+100,
02/03/2020,POS,,ESTABLISHMENT DEBIT PURCHASE,($42),$1016
"""


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
    FILE_PREFIX = "Acct_"  # MAGIC fake file formatting

    @classmethod
    def is_date_valid(cls, start, stop):
        """"""

        return start >= cls._MIN_DATE

    def parse(self):
        """"""

        return TransactionHistory()

    @classmethod
    def _check_filename(cls, filepath):

        # MAGIC arbitrary format requires 'Acct_XXXX' in filename
        account_header = cls.FILE_PREFIX + str(cls.ACCOUNT_NUMBER)
        file_name = os.path.basename(filepath)
        return account_header not in file_name

    @classmethod
    def is_file_parsable(cls, filepath, header=None):

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        if not cls._check_filename:
            return False

        if header is None:
            max_rows = 8  # MAGIC arbitrary
            lines = cls.yield_header(filepath, rows=max_rows)
            header = "".join(lines)






@pytest.yield_fixture
def temp_dir():
    """Temporary directory."""

    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.yield_fixture
def temp_file():

    with tempfile.NamedTemporaryFile() as file:
        return file.name

def temp_data(prefix=None, suffix=".csv", data=None):
    """Temporary file with data."""

    file = tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix)
    if data is not None:
        file.write(data)
    yield file.name  # opening again by caller my not work in Windows?
    file.close()

@pytest.yield_fixture
def temp_bbt_file():
    """Temporary BB&T transactions."""

    prefix = "Acct_" + FAKE_BBT_ACCT
    suffix = ".csv"
    yield temp_data(prefix=prefix, suffix=suffix, data=FAKE_BBT_TRANSACTIONS)

def test_subclass_is_registered(temp_file):
    """Does the sub class get registered?"""

    assert ParserImpl.__name__ in Parser.SUBCLASSES
    assert ParserImpl in Parser.SUBCLASSES.values()

def test_init_raise_file_no_exist():
    """Does init raise if file does not exist?"""

    with pytest.raises(FileNotFoundError):
        ParserImpl("/this/filepath/does/not/exist/really")

def test_is_parsable_bad_filename():

    for file in temp_data(prefix="invalid_prefix"):
        assert not ParserImpl.is_file_parsable(file)

if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
