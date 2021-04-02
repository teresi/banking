#!/usr/bin/env python3

"""
Helper functions.
"""

import logging
import coloredlogs
import errno
import os
import datetime


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

