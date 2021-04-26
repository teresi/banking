#!/usr/bin/env python3

"""
Test ParserFactory.
"""

import logging
import coloredlogs
import os
from itertools import chain
import tempfile

import pytest

from banking.parser import Parser
from banking.parser_factory import ParserFactory
from banking.bbt import Bbt
from banking.test_utils import bbt_file_fixture
from banking.test_utils import FAKE_BBT_TRANSACTIONS, FAKE_USAA_TRANSACTIONS

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


@pytest.fixture
def factory():

    return ParserFactory()


class FakeFiles:
    """Input files for testing."""

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


@pytest.fixture
def fake_files_fixture():
    """Default input files as a fixture."""

    with FakeFiles() as fake_files:
        yield fake_files


def test_fake_files_context():
    """Do the files get created?"""
    
    fake_files = FakeFiles()
    with fake_files as my_files:
        for path in my_files.file_paths():
            assert os.path.isfile(path)


def test_fake_files_count():
    """Do the right number of files get created?"""

    n_bbt = 3
    n_usaa = 1
    fake_files = FakeFiles(n_bbt=n_bbt, n_usaa=n_usaa)
    with fake_files as my_files:
        assert n_bbt + n_usaa == sum(1 for _ in my_files.files())


def test_init_no_throw(factory):
    """Does it initialize?"""

    pass


def test_from_file_onefile(factory, bbt_file_fixture):
    """Does it select the parser for a file, from filepath?"""

    parser = factory.from_file(bbt_file_fixture)
    assert isinstance(parser, Bbt)


def test_from_directory_onefile(factory, bbt_file_fixture):
    """Does it select the parser for a file, from directory?"""

    parent_dir = os.path.dirname(bbt_file_fixture)
    parsers = [p for p in factory.from_directory(parent_dir)]
    assert len(parsers) == 1
    assert isinstance(parsers[0], Bbt)


def test_from_directory(factory, fake_files_fixture):
    """Do the right number of parsers get produced given a directory?"""

    parent_dir = fake_files_fixture.dir.name
    parsers = [p for p in factory.from_directory(parent_dir)]
    expected = sum(1 for _ in fake_files_fixture.files())
    assert expected == len(parsers)


if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
