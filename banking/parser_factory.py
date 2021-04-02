#!/usr/bin/env python3

"""
Select which Parser to use given input files (e.g. csv).
"""

import logging

from banking.parser import Parser


class ParserFactory:
    """Creates Parser instances.

    Looks up available Parsers in the local registery to match the filename to Parser.
    """

    def __init__(self, logger=None):
        """Initializer."""

        self._logger = logger or logging.getLogger(__name__)
        self.institution_to_parsers = self._map_parsers()

        for bank, parser_list in self.institution_to_parsers.items():
            self._logger.debug(" '{}' has {} parsers".format(bank, len(parser_list)))

    def from_file(self, filepath):
        """Parser from filepath."""

        self._logger.debug("from_file:  {}".format(filepath))
        bank, account, date0, date1 = self._name_to_keys(filepath)
        parsers = self.institution_to_parsers[str.lower(bank)]
        parser = self._filter_parsers(parsers, date0, date1)
        if not parser:
            self._logger.warning("no valid parser for:  {}".format(filepath))
            return None
        return parser(filepath)

    def from_directory(self, root):
        """Yield parsers for a directory."""

        self._logger.info("reading history from {}".format(root))
        paths_ = (p for p in os.scandir(root) if os.path.isfile(p))
        paths = (p.path for p in paths_)  # posix.DirEntry --> str
        parsers = (self.from_file(p) for p in paths)

        return (p for p in parsers if p)  # remove None entries

    def parser_names(self):
        """Return map of institution to Parser class names; for debugging.

        Returns:
            dict(str, list(str)):  the institution map to parser class names.
        """

        institution_to_parser_names = defaultdict(list)
        for bank, parser_list in self.institution_to_parsers.items():
            institution_to_parser_names[bank].append([p.__name__ for p in parser_list])
        return institution_to_parser_names

    @staticmethod
    def parse_date(date):  # TODO delete, refactoring out storing dates in filenames
        """Parse a duration from the date field of the filename.

        Expects '<date_0>-<date_1>'.
        """

        try:
            date0, date1 = date.split("-")
        except ValueError as verr:
            msg = " expected 2 '-' delimited fields in the date; {}".format(str(verr))
            raise ValueError(msg)

        return date0, date1

    @classmethod
    def _map_parsers(cls):
        """Dict of name of bank to iterable of Parsers.

        Requires caller to import all relevant Parser sub classes prior to invoking.
        """

        parser_dict = defaultdict(list)
        for parser_name, parser_class in _registry.items():
            if parser_class.INSTITUTION == str.lower(str(None)):
                continue
            parser_dict[parser_class.INSTITUTION].append(parser_class)
        return parser_dict

    @classmethod
    def _name_to_keys(cls, filepath):  # TODO delete, refactoring out storing this info in filename
        """Return various identifiers from the transaction history filename.

        Expects '<bank>_<account>_<date_0>-<date_1>.<ext>'.
        """

        file_base = os.path.basename(filepath)
        file_name, ext = os.path.splitext(file_base)
        bank, account, date = cls._parse_path(file_name)
        date0, date1 = Parser.parse_date(date)

        return bank, account, date0, date1

    @staticmethod
    def _parse_path(filepath):  # TODO delete, refactoring out storing this info in filename
        """Return various identifiers from the transaction history filename.

        Expects '<bank>_<account>_<date>.<ext>'.
        """

        base = os.path.basename(str(filepath))
        filename, ext = os.path.splitext(base)
        fields = filename.split("_")
        try:
            bank, account, date = fields
        except ValueError as verr:
            msg = " expected bank, account, date '_' delimited fields in filename; {}".format(
                filepath
            )
            raise ValueError(msg)

        return bank, account, date

    def _filter_parsers(self, parsers, date0, date1):  # TODO delete, refactoring out storing this info in filename
        """Filter the parser iterable for the time frame."""

        valid_parsers = [p for p in parsers if p.is_date_valid(date0, date1)]
        if len(valid_parsers) > 1:
            msg = "more than one parser exists for {} between {}...{}".format(
                institution, date0, date1
            )
            logger.error(msg)
            msg = "these parsers overlap in time and are ambiguous: {}".format(
                valid_parsers
            )
            logger.info(msg)
            return None
        return valid_parsers[0] if valid_parsers else None

