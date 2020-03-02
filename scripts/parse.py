#!/usr/bin/env python3

import os
import logging

import coloredlogs

from banking import transaction
from banking.parser import Parser, ParserFactory
from banking.usaa import UsaaParser1
from banking.bbt import BbtParser1

#NOTE parser classes must be imported for the factory to work...
# but the versioning hasn't started yet, and separately that is a little confusing
# is there a better way? import in module.__init__?


if __name__ == "__main__":
    
    import argparse

    file_dir = os.path.dirname(__file__)
    default_history_dir = os.path.join(file_dir, '../../banking_history')

    parser = argparse.ArgumentParser(description='display transaction history')
    parser.add_argument('--dir', type=str, default=default_history_dir,
                        help='directory of exported debit / credit history')
    parser.add_argument('--filter', type=str, default=None, nargs='+',
                        help='filter histories by folder prefixes')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help='verbosity: None = warn, -v = info, -vv = debug')
    args = parser.parse_args()
    
    verb_levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    verb = verb_levels[min(len(verb_levels)-1, args.verbose)]
    logger = logging.getLogger(__name__)
    coloredlogs.install(level=verb)
    logger.debug("arguments:  {}".format(args))

    factory = ParserFactory()

    parsers_available = factory.parser_names()
    for institution, parser_names in factory.parser_names().items():
        logger.info("{} has parsers: {}".format(institution, parser_names))

    for sub in os.listdir(args.dir):
        logger.info("found dir:  {}".format(sub))
        directory = os.path.join(args.dir, sub)
        parsers = factory.from_directory(directory)

        for p in parsers:
            
            logging.debug("\tparser for dir: {}".format(p))
            p.parse()

    
 
