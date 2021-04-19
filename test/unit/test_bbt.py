#!/usr/bin/env python3

"""
Test BBT Parser implementation.
"""

import logging
import tempfile
import coloredlogs
from datetime import date
import os
from contextlib import contextmanager
from decimal import Decimal
import random, string

import pytest
import pandas

from banking.parser import Parser
from banking.bbt import Bbt
from banking.bbt import _convert_price, _convert_date, _convert_check
from banking.bbt import _convert_posted_balance
from banking.utils import file_dne_exc
from banking.utils import TransactionColumns, TransactionCategories
from banking.test_utils import bbt_file, FAKE_BBT_TRANSACTIONS

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


@pytest.fixture
def bbt_instance(bbt_file):

    yield Bbt(bbt_file)


@pytest.fixture
def bbt_frame(bbt_instance):
    """Parsed data frame from fake data."""

    frame = bbt_instance.parse()
    yield frame


def expected_filename():
    """A valid input filename for the parser."""

    # MAGIC our convention, starts with 
    return Bbt.FILE_PREFIX + str(Bbt.ACCOUNT) + '_' + rand_string(8)


def rand_string(count):
    """A random string of lower case letters."""

    return ''.join([random.choice(string.ascii_lowercase) for i in range(count)])


def test_convert_price_pos():
    """Does a valid credit get converted?"""

    assert Decimal('1.23') == _convert_price("$+1.23")


def test_convert_price_neg():
    """Does a valid debt get converted?"""

    assert Decimal('-2.34') == _convert_price("($2.34)")


def test_convert_posted():
    """Does a valid posted balance get converted?"""

    assert Decimal("42.42") == _convert_posted_balance("$42.42")


def test_reject_credit():
    """Does an invalid credit get rejected?"""

    assert None == _convert_price("+100")


def test_reject_debit():
    """Does an invalid debit get rejected?"""

    assert None == _convert_price("$9000")


def test_convert_date():
    """Does a valid date get converted?"""

    assert date(2020,1,2) == _convert_date("01/02/2020")


def test_convert_check():
    """Does a valid check number get converted?"""

    assert 9000 == _convert_check("9000")


def test_reject_check():
    """Does a missing check get converted?"""

    assert _convert_check('') is -1


@pytest.mark.skip(reason="work in progress")
def test_convert_categories():
    """Do the categories get populated from the descriptions?"""

    raise NotImplementedError("work in progress")


def test_transaction_fields():
    """Does the mapping have feasible entries?"""

    our_names = [c.name for c in TransactionColumns]
    for bbt, ours in Bbt.field_2_transaction().items():
        assert bbt in Bbt.field_names()
        assert ours in our_names


def test_check_filename():
    """Does a valid filename pass?"""

    assert Bbt._check_filename(expected_filename())


def test_reject_filename():
    """Does an invalid filename get rejected?"""

    # MAGIC offset account no.
    filename = str(12345) + expected_filename()
    assert not Bbt._check_filename(filename)


def test_check_filename():
    """Does a valid filename pass?"""

    assert Bbt._check_filename(expected_filename())


def test_check_filename_path():
    """Does a valid file path pass?"""

    path = os.path.join("/", "arbitrary", "dir", expected_filename())
    assert Bbt._check_filename(path)


def test_check_filename_reject():
    """Does an invalid filename get rejected?"""

    bad_filename = rand_string(4) + expected_filename()
    assert not Bbt._check_filename(bad_filename)


def test_parse(bbt_file):
    """Does a normal file get parsed?"""

    assert Bbt.is_file_parsable(bbt_file)
    frame = Bbt(bbt_file).parse()
    rows, cols = frame.shape
    # MAGIC minus 1 for the header
    assert rows == FAKE_BBT_TRANSACTIONS.count('\n') - 1


def test_posted_balance(bbt_frame):
    """Does the posted balance get read correctly?"""

    cat = TransactionColumns.POSTED_BALANCE.name
    posted = [val for val in bbt_frame[cat] if val is not None]
    parsed = posted[-1]
    # MAGIC hand calc from above fake data
    assert parsed == Decimal('1016')


def test_check_number(bbt_frame):
    """Does the check number get read correctly?"""

    # MAGIC hand calc from above fake data
    expected = [-1, -1, -1, -1, 301]
    assert all(expected == bbt_frame[TransactionColumns.CHECK_NO.name])
    

def test_convert_category_sanity_check(bbt_frame):
    """Do the categories get mapped for our fake data?

    This is only an initial check.
    """

    # MAGIC hand calc from above fake data
    expected = ['salary', 'groceries', 'unknown', 'medical', 'unknown']
    cat = TransactionColumns.CATEGORY.name
    unkown = str(TransactionCategories.UNKNOWN.name)
    parsed = []
    for i, row in bbt_frame.iterrows():
        input = row[cat]
        parsed.append(input.lower())
    assert expected == parsed


def test_fill_bank(bbt_instance):
    """Does the bank name get populated?"""

    frame = bbt_instance.parse()
    assert all(frame[TransactionColumns.BANK.name] == bbt_instance.INSTITUTION)


def test_fill_account(bbt_instance):
    """Does the bank account get populated?"""

    frame = bbt_instance.parse()
    assert all(frame[TransactionColumns.ACCOUNT.name] == bbt_instance.ACCOUNT)
