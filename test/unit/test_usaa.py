#!/usr/bin/env python3

"""
Test USAA Parser implementation.
"""

import logging
from decimal import Decimal
from datetime import date

from banking.usaa import _convert_price, _convert_date
from banking.test_utils import FAKE_USAA_TRANSACTIONS

def test_convert_price_pos():
    """Does a valid credit get converted?"""

    assert Decimal('1.23') == _convert_price("--1.23")


def test_convert_price_neg():
    """Does a valid debt get converted?"""

    assert Decimal('-2.34') == _convert_price("-2.34")

def test_reject_credit():
    """Does an invalid credit get rejected?"""

    assert None == _convert_price("100")


def test_reject_debit():
    """Does an invalid debit get rejected?"""

    assert None == _convert_price("$9000")


def test_convert_date():
    """Does a valid date get converted?"""

    assert date(2020,1,2) == _convert_date("01/02/2020")

