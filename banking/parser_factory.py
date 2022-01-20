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

        # MAGIC 0 b/c there can only be one parser now
        return parsers[0](filepath)

    def _scrape_files(self, root):
        """Recursivly yield all files from directory, excluding directories.

        Yields:
            (os.DirEntry) objects
        """

        for file in os.scandir(root):
            if not file.is_dir():
                yield file
            else:
                yield from self._scrape_files(file.path)

    def from_directory(self, root):
        """Map parsers to the input files in a directory."""

        self._logger.info("reading history from {}".format(root))
        # TODO filter files based on extension (e.g. csv/txt)?
        paths_ = (p for p in self._scrape_files(root))
        paths = [p.path for p in paths_]  # posix.DirEntry --> str
        self._logger.debug("found: %s" % paths)
        if not paths:
            msg = "no input files found in %s, cannot parse transaction data"
            self._logger.warning(msg % root)
        file_to_parsers = {_f: self.from_file(_f) for _f in paths}
        file_to_parsers = {_f: _p for _f, _p in file_to_parsers.items() if _p}

        self._logger.debug("file to parsers: {}".format(file_to_parsers))
        return file_to_parsers

    # TODO yield files based on extension white list?
    def _filter_file_by_ext(dir, extensions):
        pass
