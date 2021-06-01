#!/usr/bin/env python3


"""
Helper functions and data for testing.
"""

from contextlib import contextmanager
from itertools import chain
import os
import tempfile

import pytest

from banking.bbt import Bbt
from banking.usaa import Usaa

FAKE_BBT_TRANSACTIONS="""Date,Transaction Type,Check Number,Description,Amount,Daily Posted Balance
01/01/2020,Credit,,LEGIT EMPLOYER SALARY,$+1000,$0.00
01/02/2020,Debit,,KROGER STORE DEBIT CARD,($42),$958
02/01/2020,Deposit,,TRANSFER FROM,$+100,
02/03/2020,POS,,WALGREENS DEBIT PURCHASE,($42),$1016
02/05/2020,POS,301,Check Payment,($42),
"""


FAKE_USAA_TRANSACTIONS="""forecasted,,01/01/2020,,FUNDS TRANSFER,Uncategorized,-3.50
posted,,01/02/2020,,LEGIT EMPLOYER SALARY,Paychecks/Salary,1000
posted,,01/03/2020,,LEGIT WASTE SERVICE,Utilities,-20.25
posted,,01/04/2020,,LEGIT FOOD SERVICE,Groceries,-35.56
posted,,01/10/2020,,INTEREST PAID,Interest,0.05
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


@contextmanager
def bbt_file():
    """Filepath to fake BBT data."""

    prefix = Bbt.FILE_PREFIX + str(Bbt.ACCOUNT) + "_"
    data = FAKE_BBT_TRANSACTIONS
    with temp_data(prefix=prefix, suffix=".csv", data=data) as path:
        yield path


@pytest.fixture
def bbt_file_fixture():
    """Pytest fixture to filepath to fake BBT data."""

    with bbt_file() as file:
        yield file


@contextmanager
def usaa_file():
    """Filepath to fake USAA data."""

    data = FAKE_USAA_TRANSACTIONS
    with temp_data(suffix=".csv", data=data) as path:
        yield path


@pytest.fixture
def usaa_file_fixture():
    """Pytest fixture to filepath to fake USAA data."""

    with usaa_file() as file:
        yield file


class FakeFiles:
    """Input files for testing."""
    # FUTURE register parser/fake data on runtime instead of hard coded here

    def __init__(self, n_bbt=2, n_usaa=2):
        """Initialize.

        Args:
            n_bbt(int): how many bbt files to create
            n_usaa(int): how many usaa files to create
        """

        self.n_bbt = n_bbt
        self.n_usaa = n_usaa

        self._bbt_files = []
        self._usaa = []
        self.dir = None

    def file_paths(self):
        """List of paths to the files.

        Raises:
            RuntimeError: files have not yet been instantiated, use context mgr
        """

        return [f.name for f in self.files()]

    def files(self):
        """List of the files.

        Raises:
            RuntimeError: files have not yet been instantiated, use context mgr
        """

        if self.dir is None:
            raise RuntimeError("enter this instance prior to accessing the files")

        return [f for f in chain(self._bbt_files, self._usaa_files)]

    def __enter__(self):
        """Context manager begin."""

        self.dir = tempfile.TemporaryDirectory()

        bbt_prefix = Bbt.FILE_PREFIX + str(Bbt.ACCOUNT)
        bbt_data = FAKE_BBT_TRANSACTIONS
        self._bbt_files = [self._write(bbt_data, bbt_prefix) for i in range(self.n_bbt)]

        usaa_data = FAKE_USAA_TRANSACTIONS
        self._usaa_files = [self._write(usaa_data) for i in range(self.n_usaa)]

        return self

    def _write(self, data, prefix=None, suffix=".csv"):
        """A file with data."""

        file = tempfile.NamedTemporaryFile(
            dir=self.dir.name,
            prefix=prefix,
            suffix=suffix,
            mode='w+',  # MAGIC writing strings
            delete=False,  # MAGIC Parser will read/close, so don't delete there
        )
        file.write(data)
        file.seek(0)
        return file

    def __exit__(self, exc_type, exc_val, exc_trace):
        """Context manager end."""

        map(lambda f: f.close(), self.files())
        map(os.remove, self.file_paths())
        self.dir.cleanup()
        self.dir = None
