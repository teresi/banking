#!/usr/bin/env python3

"""
Test ParserFactory.
"""

import logging
import coloredlogs
import os

import pytest

from banking.parser import Parser
from banking.parser_factory import ParserFactory
from banking.bbt import Bbt
from banking.test_utils import bbt_file

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


@pytest.fixture
def factory():

    return ParserFactory()

def test_init_no_throw(factory):
    """Does it initialize?"""

    pass

def test_from_file_onefile(factory, bbt_file):
    """Does it select the parser for one file?"""

    parent_dir = os.path.dirname(bbt_file)
    parser = factory.from_file(bbt_file)
    assert isinstance(parser, Parser)



if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
