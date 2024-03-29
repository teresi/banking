#!/usr/bin/env python3

import os
import logging

import coloredlogs

from banking.utils import setup_logger
from banking.parser import Parser
from banking.parser_factory import ParserFactory
from banking.bbt import Bbt
from banking.usaa import Usaa


def select_log_level(count):
    """Maps the counter from argparse to the verbosity level."""

    level = {
        2: 'DEBUG',
        1: 'INFO',
        0: 'WARNING'
    }
    return level.get(count, 'DEBUG')


if __name__ == "__main__":

    import argparse

    file_dir = os.path.dirname(__file__)
    default_history_dir = os.path.join(file_dir, '..', 'banking_history')

    arg_parser = argparse.ArgumentParser(description='display transaction history')
    arg_parser.add_argument('--dir', type=str, default=default_history_dir,
                        help='directory of exported debit / credit history')
    arg_parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='verbosity: None = warn, -v = info, -vv = debug')
    args = arg_parser.parse_args()

    setup_logger(args.verbose)
    logger = logging.getLogger(__name__)
    level = select_log_level(args.verbose)
    coloredlogs.install(level=level, logger=logger)
    logger.debug("arguments:  {}".format(args))

    factory = ParserFactory()

    for filepath, parser in factory.from_directory(args.dir).items():
        transactions = parser.parse()
        logging.info("\tfile:     {}".format(transactions.path))
        print("{}\n".format(transactions.frame))

