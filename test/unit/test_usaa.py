#!/usr/bin/env python3

"""
Test USAA Parser implementation.
"""

import logging
from decimal import Decimal
import datetime
import pytest
import os

from banking.usaa import Usaa, _convert_price, _convert_date
from banking.utils import TransactionColumns
from banking.test_utils import FAKE_USAA_TRANSACTIONS
from banking.test_utils import usaa_file, usaa_file_fixture
from banking.test_utils import temp_data, bbt_file_fixture


LOGGER = logging.getLogger(os.path.basename(__file__))

FAKE_USAA_TRANSACTIONS_BAD_="""forecasted,,01/01/2020,,FUNDS TRANSFER,Uncategorized,-3.50
posted,,01/02/2020,,LEGIT EMPLOYER SALARY,Paychecks/Salary,1000
posted,,01/03/2020,,LEGIT WASTE SERVICE,Utilities,-20.25
posted,,01/04/2020,,LEGIT FOOD SERVICE,Groceries,-35.56
posted,,01/10/2020,,INTEREST PAID,Interest,0.05
posted,,01/11/2020,,LEGIT FOOD SERVICE,Groceries,-122.25
"""
FAKE_USAA_GOOD_LINE_PLUS = "posted,,01/11/2020,,LEGIT FOOD SERVICE,Groceries,123.45"
FAKE_USAA_GOOD_LINE_MINUS = "posted,,01/11/2020,,LEGIT CREDIT,Groceries,-123.45"
FAKE_USAA_BAD_LINE = "not-posted,,01%11%2020,,LEGIT FOOD SERVICE,Groceries,xx123.45"
FAKE_USAA_EXTRA_COL = "posted,null,01/11/2020,null,detail,category,price,EXTRA COLUMN"
FAKE_USAA_MISSING_COL = "posted,null,01/11/2020,null,detail,category"
FAKE_USAA_BAD_DATE = "posted,null,X_BAD_DATE_X,null,detail,category,-42.00"
FAKE_USAA_BAD_AMOUNT = "posted,null,02/12/2020,null,detail,category,X_BAD_AMOUNT_X"


@pytest.fixture
def usaa_instance(usaa_file_fixture):
    """An instance of Usaa."""

    yield Usaa(usaa_file_fixture)


def test_convert_price_pos():
    """Does a valid credit get converted?"""

    assert Decimal('1.23') == _convert_price("1.23")


def test_convert_price_neg():
    """Does a valid debt get converted?"""

    assert Decimal('-2.34') == _convert_price("-2.34")

def test_reject_credit():
    """Does an invalid credit get rejected?"""

    assert None == _convert_price("$100")


def test_reject_debit():
    """Does an invalid debit get rejected?"""

    assert None == _convert_price("$9000")


def test_reject_alpha():
    """Does a non-number get rejected?"""

    assert None == _convert_price("abcdef")


def test_convert_date():
    """Does a valid date get converted?"""

    assert datetime.date(2020,1,2) == _convert_date("01/02/2020")


@pytest.mark.skip(reason="work in progress")
def test_category_no_throw():
    """Does the category succeed?"""

    raise NotImplementedError("work in progress")


def test_init():
    """Does initialization succeed?"""

    with usaa_file() as path:
        Usaa(path)


def test_init_fixture(usaa_file_fixture):
    """Does initialization with the fixture succeed?"""

    Usaa(usaa_file_fixture)


def test_transaction_fields():
    """Are the USAA columns mapped to the TransactionColumns?

    This is done to standardize the final parsed history.
    """
    
    standard_col_headers = [c.name for c in TransactionColumns]
    for usaa, ours in Usaa.field_2_transaction().items():
        assert usaa in Usaa.field_names()
        assert ours in standard_col_headers


def test_check_amount():
    """Does a good amount value pass?"""

    assert Usaa.check_amount_column(FAKE_USAA_GOOD_LINE_PLUS)
    assert Usaa.check_amount_column(FAKE_USAA_GOOD_LINE_MINUS)


def test_check_amount_reject():
    """Does a bad amount value fail?"""

    assert not Usaa.check_amount_column(FAKE_USAA_BAD_LINE)


def test_check_date():
    """Does a good date pass?"""

    assert Usaa.check_date_column(FAKE_USAA_GOOD_LINE_PLUS)


def test_check_date_reject():
    """Does a bad date value fail?"""

    assert not Usaa.check_date_column(FAKE_USAA_BAD_LINE)


def test_is_file_parsable(usaa_file_fixture):
    """Does a good file pass the check?"""

    assert Usaa.is_file_parsable(usaa_file_fixture)


def test_is_file_parsable_reject():
    """Does a file with bad contents get rejected?"""

    data = FAKE_USAA_BAD_LINE
    with temp_data(prefix=None, suffix=".csv", data=data) as path:
        assert not Usaa.is_file_parsable(path)


def test_is_file_parsable_bbt(bbt_file_fixture):
    """Does a file meant for another parser get rejected?"""

    assert not Usaa.is_file_parsable(bbt_file_fixture)


def test_get_field_date():
    """Is a date parsed correctly for a line?

    NB the 'date' column is used to validate an input file, so it should be tested
    """

    # MAGIC should match the fake value
    expected = datetime.datetime.strptime("01/11/2020", "%m/%d/%Y").date()
    assert expected == Usaa.get_field(FAKE_USAA_GOOD_LINE_PLUS, Usaa._DATE_COL_NAME)


def test_run_parse_checks_col_count():
    """Does a bad column count get rejected?"""

    path = "FAKE_PATH_FOR_TESTING"
    assert not Usaa._run_parse_checks(FAKE_USAA_EXTRA_COL, path, LOGGER)
    assert not Usaa._run_parse_checks(FAKE_USAA_MISSING_COL, path, LOGGER)


def test_run_parse_checks_date_col():
    """Does a bad date value get rejected?"""

    path = "FAKE_PATH_FOR_TESTING"
    assert not Usaa._run_parse_checks(FAKE_USAA_BAD_DATE, path, LOGGER)


def test_run_parse_checks_amount_col():
    """Does a bad debit/credit value get rejected?"""

    path = "FAKE_PATH_FOR_TESTING"
    assert not Usaa._run_parse_checks(FAKE_USAA_BAD_AMOUNT, path, LOGGER)


def test_get_field_amount():
    """Is an amount parsed correctly for a line?

    NB the 'amount' column is used to validate an input file, so it should be tested
    """

    # MAGIC should match the fake value
    expected = Decimal('123.45')
    assert expected == Usaa.get_field(FAKE_USAA_GOOD_LINE_PLUS, Usaa._AMOUNT_COL_NAME)

