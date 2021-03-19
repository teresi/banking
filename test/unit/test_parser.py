#!/usr/bin/env python3

"""
Test ParserBase
"""

import logging
import tempfile
import coloredlogs
import datetime

import pytest

from banking.parser import Parser
from banking.transaction import TransactionColumns, TransactionHistory

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


class ParserImpl(Parser):

    _MIN_DATE = datetime.date(1970, 1, 1)  # MAGIC arbirtrary

    VERSION = 1
    INSTITUTION = "Super Fake Bank"
    DELIMETER = ","
    FIELD_NAMES = ["date", "amount", "note"]
    FIELD_2_TRANSACTION = {
        "date": TransactionColumns.DATE.name,
        "note": TransactionColumns.DESCRIPTION.name,
        "amount": TransactionColumns.AMOUNT.name,
    }

    @classmethod
    def is_date_valid(cls, start, stop):
        """"""
        return start >= cls._MIN_DATE

    def parse(self):
        """"""
        return TransactionHistory()


@pytest.yield_fixture
def temp_dir():
    """Temporary directory."""

    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.yield_fixture
def temp_file():
    """Temporary file."""

    with tempfile.NamedTemporaryFile(suffix="."+"txt") as temp_file:
        yield temp_file.name

def test_subclass_is_registered(temp_file):
    """Does the sub class get registered?"""

    assert ParserImpl.__name__ in Parser.SUBCLASSES
    assert ParserImpl in Parser.SUBCLASSES.values()


if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
