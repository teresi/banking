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
from banking.test_utils import bbt_file_fixture, FakeFiles
from banking.test_utils import FAKE_BBT_TRANSACTIONS, FAKE_USAA_TRANSACTIONS

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


@pytest.fixture
def factory():

    return ParserFactory()


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


def test_from_directory(factory, fake_files_fixture):
    """Do the right number of parsers get produced given a directory?"""

    parent_dir = fake_files_fixture.dir.name
    file_to_parser = factory.from_directory(parent_dir)
    parsers = file_to_parser.values()
    expected = sum(1 for _ in fake_files_fixture.files())
    assert expected == len(parsers)



if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
