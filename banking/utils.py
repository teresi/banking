#!/usr/bin/env python3

"""
Helper functions.
"""

import logging
import coloredlogs
import errno
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
