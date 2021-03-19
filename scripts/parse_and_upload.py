#!/usr/bin/env python3

"""
Process and upload banking history to the Google Sheet.
"""

import argparse
import os
import logging

import colored_logs

from banking.utils import setup_logger
from banking.google_sheets import Sheet
from banking.parser import 


if __name__ == "__main__":
    
    file_dir = os.path.dirname(__file__)
    default_history_dir = os.path.join(file_dir, '../../banking_history')

    parser = argparse.ArgumentParser(description='read, parse, upload, transactions')
    parser.add_argument('config', type=str,
                        help='path to configuration file')
    parser.add_argument('-h', '--history', type=str, default=default_history_dir,
                        help='directory of exported debit / credit history')
    parser.add_argument('-v', '--verbose', action='count', default=2,
                        help='verbosity: None = warn, -v = info, -vv = debug')
    args = parser.parse_args()

    setup_logger(args.verbose)
    logger = logging.getLogger(__name__)
    logger.debug("arguments:  {}".format(args))



