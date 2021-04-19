#!/usr/bin/env python3

"""
Select which Parser to use given input files (e.g. csv).
"""

import logging
from collections import defaultdict

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

        parsers = []
        # MAGIC experimental, enough rows to approximate content format
        start_of_file = [line for line in Parser.yield_header(filepath, rows=8)]
        lines = '\n'.join(start_of_file)
        for name, klass in self._parsers.items():
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
        """Yield parsers for a directory."""

        self._logger.info("reading history from {}".format(root))
        paths_ = (p for p in os.scandir(root) if os.path.isfile(p))
        paths = (p.path for p in paths_)  # posix.DirEntry --> str
        parsers = (self.from_file(p) for p in paths)
        return (p for p in parsers if p)  # remove None entries

# TODO delete? this isn't as useful due to the refactor
#    def parser_names(self):
#        """Return map of institution to Parser class names; for debugging.
#
#        Returns:
#            dict(str, list(str)):  the institution map to parser class names.
#        """
#
#        institution_to_parser_names = defaultdict(list)
#        for bank, parser_list in self.institution_to_parsers.items():
#            institution_to_parser_names[bank].append([p.__name__ for p in parser_list])
#        return institution_to_parser_names

# TODO delete, not reading dates like this anymore
#    @staticmethod
#    def parse_date(date):
#        """Parse a duration from the date field of the filename.
#
#        Expects '<date_0>-<date_1>'.
#        """
#
#        try:
#            date0, date1 = date.split("-")
#        except ValueError as verr:
#            msg = " expected 2 '-' delimited fields in the date; {}".format(str(verr))
#            raise ValueError(msg)
#
#        return date0, date1

# TODO delete, the Parser exposes a dict of the sub classes
#    @classmethod
#    def _map_parsers(cls):
#        """Dict of name of bank to iterable of Parsers.
#
#        Requires caller to import all relevant Parser sub classes prior to invoking.
#        """
#
#        parser_dict = defaultdict(list)
#        for parser_name, parser_class in Parser.gen_subclasses():
#            if parser_class.INSTITUTION is None:
#                continue
#            parser_dict[parser_class.INSTITUTION].append(parser_class)
#        return parser_dict

# TODO delete, don't store (much) info in filename
#    @classmethod
#    def _name_to_keys(cls, filepath):
#        """Return various identifiers from the transaction history filename.
#
#        Expects '<bank>_<account>_<date_0>-<date_1>.<ext>'.
#        """
#
#        file_base = os.path.basename(filepath)
#        file_name, ext = os.path.splitext(file_base)
#        bank, account, date = cls._parse_path(file_name)
#        date0, date1 = Parser.parse_date(date)
#
#        return bank, account, date0, date1

# TODO remove, don't store (much) info in the filename
#    @staticmethod
#    def _parse_path(filepath):  # TODO delete, refactoring out storing this info in filename
#        """Return various identifiers from the transaction history filename.
#
#        Expects '<bank>_<account>_<date>.<ext>'.
#        """
#
#        base = os.path.basename(str(filepath))
#        filename, ext = os.path.splitext(base)
#        fields = filename.split("_")
#        try:
#            bank, account, date = fields
#        except ValueError as verr:
#            msg = " expected bank, account, date '_' delimited fields in filename; {}".format(
#                filepath
#            )
#            raise ValueError(msg)
#
#        return bank, account, date

# TODO refactor, not checking the dates this way anymore
#    def _filter_parsers(self, parsers, date0, date1):
#        """Filter the parser iterable for the time frame."""
#
#        valid_parsers = [p for p in parsers if p.is_date_valid(date0, date1)]
#        if len(valid_parsers) > 1:
#            msg = "more than one parser exists for {} between {}...{}".format(
#                institution, date0, date1
#            )
#            logger.error(msg)
#            msg = "these parsers overlap in time and are ambiguous: {}".format(
#                valid_parsers
#            )
#            logger.info(msg)
#            return None
#        return valid_parsers[0] if valid_parsers else None

