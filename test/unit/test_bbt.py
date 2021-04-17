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

import pytest
import pandas

from banking.parser import Parser
from banking.bbt import Bbt
from banking.bbt import _convert_price, _convert_date, _convert_check
from banking.utils import file_dne_exc, TransactionColumns

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)

FAKE_TRANSACTIONS="""Date,Transaction Type,Check Number,Description,Amount,Daily Posted Balance
01/01/2020,Credit,,LEGIT EMPLOYER,$+1000,$0.00
01/02/2020,Debit,,ESTABLISHMENT STORE DEBIT CARD,($42),$958
02/01/2020,Deposit,,TRANSFER FROM,$+100,
02/03/2020,POS,,ESTABLISHMENT DEBIT PURCHASE,($42),$1016
02/05/2020,POS,301,Check Payment,($42),
"""


def test_convert_price_pos():
    """Does a valid credit get converted?"""

    assert Decimal('1.23') == _convert_price("$+1.23")


def test_convert_price_neg():
    """Does a valid debt get converted?"""

    assert Decimal('-2.34') == _convert_price("($2.34)")


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

    assert _convert_check('') is None


def test_transaction_fields():
    """Does the mapping have feasible entries?"""

    our_names = [c.name for c in TransactionColumns]
    for bbt, ours in Bbt.FIELD_2_TRANSACTION.items():
        assert bbt in Bbt.FIELD_NAMES
        assert ours in our_names


def test_check_filename():
    """Does a valid filename pass?"""

    assert Bbt._check_filename("Acct_7389_XXXX_XXXX.CSV")


def test_reject_filename():
    """Does an invalid filename get rejected?"""

    assert not Bbt._check_filename("Acct_9999.csv")


def test_parse():
    """Does a normal file get parsed?"""




