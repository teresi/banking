#!/usr/bin/env python3

"""
Select which Parser to use given input files (e.g. csv).
"""

import logging
from collections import defaultdict
import os

import pytest

from banking.parser import Parser


class ParserFactory:
    """Creates Parser instances.

    NB Implementations of Parser are registered using the meta class, therefore
    you must import all your parser implementations prior to calling the factory.
    """

    def __init__(self, logger=None):
        """Initializer."""

        self._logger = logger or logging.getLogger(__name__)
        self._parsers = {name: klass for name, klass in Parser.gen_implementations()}

        self._logger.debug("imported %i parsers" % sum(1 for _ in self._parsers))
        for name, parser in self._parsers.items():
            self._logger.debug("  parser %s:  %s" % (name, parser))

    def from_file(self, filepath):
        """Parser from filepath."""

        self._logger.debug("reading header of %s" % filepath)
        parsers = []
        # MAGIC experimental, enough rows to approximate content format
        start_of_file = [line for line in Parser.yield_header(filepath, rows=8)]
        lines = '\n'.join(start_of_file)
        for name, klass in self._parsers.items():
            self._logger.debug("try %s for file %s" % (klass, filepath))
            if klass.is_file_parsable(filepath, beginning=lines):
                parsers.append(klass)

        if not parsers:
            self._logger.error("cannot parse, no valid parser for:  {}"
                               .format(filepath))
            return None
        if len(parsers) != 1:
            msg = ("multiple parsers available for file %s:  %s"
                   % (filepath, parsers))
            self._logger.critical(msg)
            raise RuntimeError(msg)

        return parsers[0](filepath)

    def from_directory(self, root):
        """Map parsers to the input files in a directory."""

        self._logger.info("reading history from {}".format(root))
        # TODO filter files based on extension (e.g. csv/txt)
        paths_ = (p for p in os.scandir(root) if os.path.isfile(p))
        paths = (p.path for p in paths_)  # posix.DirEntry --> str
        file_to_parsers = {p: self.from_file(p) for p in paths}
        return file_to_parsers

    # TODO yield files based on extension white list
    def _filter_file_by_ext(dir, extensions):
        pass
