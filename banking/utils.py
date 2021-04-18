#!/usr/bin/env python3


"""
Helper functions and data.
"""


import datetime
import errno
from enum import Enum, unique, auto
from contextlib import contextmanager
import tempfile
import logging
import coloredlogs
import os


def file_dne_exc(filepath):
    """Return FileNotFoundError given a filepath."""

    return FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), filepath)


def setup_logger(level):
    """Helper to turn on colored logging to stdout.

    Args:
        level (int): [0,1,2] mapped to [Warning, Info, Debug]
    """

    verb_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verb = verb_levels[min(len(verb_levels) - 1, level)]
    coloredlogs.install(level=verb)

def last_day_of_month(day):
    """The last day of the month from the date provided.

    Args:
        day(datetime.datetime): a date
    """

    next_month = day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


@unique
class TransactionColumns(Enum):
    """The names for the columns present in a TransactionHistory data frame."""

    DATE = auto()
    CHECK_NO = auto()
    AMOUNT = auto()
    DESCRIPTION = auto()
    BANK = auto()
    ACCOUNT = auto()
    CATEGORY = auto()
    POSTED_BALANCE = auto()

    @classmethod
    def names(cls):
        return (col.name for col in cls)


@unique
class TransactionCategories(Enum):

    UNKNOWN = auto()
    SALARY = auto()
    HOUSING = auto()
    RETIREMENT = auto()
    INVESTMENTS = auto()
    MEDICAL = auto()
    VEHICLES = auto()
    COMMUNICATIONS = auto()
    HOUSEHOLD = auto()
    GROCERIES = auto()
    RESTARAUNTS = auto()
    TAXES = auto()
    PERSONAL = auto()



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
        yield file.name  # opening again by caller my not work in Windows?



