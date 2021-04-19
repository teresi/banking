#!/usr/bin/env python3


"""
Helper functions and data for testing.
"""

from contextlib import contextmanager
import tempfile

import pytest

from banking.bbt import Bbt

FAKE_BBT_TRANSACTIONS="""Date,Transaction Type,Check Number,Description,Amount,Daily Posted Balance
01/01/2020,Credit,,LEGIT EMPLOYER SALARY,$+1000,$0.00
01/02/2020,Debit,,KROGER STORE DEBIT CARD,($42),$958
02/01/2020,Deposit,,TRANSFER FROM,$+100,
02/03/2020,POS,,WALGREENS DEBIT PURCHASE,($42),$1016
02/05/2020,POS,301,Check Payment,($42),
"""


FAKE_USAA_TRANSACTIONS="""forecasted,,01/01/2020,,FUNDS TRANSFER,Uncategorized,-3.50
posted,,01/02/2020,,LEGIT EMPLOYER SALARY,Paychecks/Salary,--1000
posted,,01/03/2020,,LEGIT WASTE SERVICE,Utilities,-20.25
posted,,01/04/2020,,LEGIT FOOD SERVICE,Groceries,-35.56
posted,,01/10/2020,,INTEREST PAID,Interest,--0.05
posted,,01/11/2020,,LEGIT FOOD SERVICE,Groceries,-122.25
"""


@pytest.fixture
def temp_dir():
    """Temporary directory as a pytest fixture."""

    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file():
    """Temporary file as a pytest fixture."""

    with tempfile.NamedTemporaryFile() as file:
        return file.name


@contextmanager
def temp_data(prefix=None, suffix=".csv", data=None):
    """Temporary file with data.

    Args:
        prefix(str): filename prefix
        suffix(str): filename extension
        data(str): write data to the file

    Yields:
        (filehandle) the file (
    """

    with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, mode='w+') as file:
        if data is not None:
            file.write(data)
        file.seek(0)
        yield file.name  # CAVEAT opening again by caller my not work in Windows?


@pytest.fixture
def bbt_file():
    """Filepath to fake data."""

    prefix = Bbt.FILE_PREFIX + str(Bbt.ACCOUNT)
    data = FAKE_BBT_TRANSACTIONS
    with temp_data(prefix=prefix, suffix=".csv", data=data) as path:
        yield path

