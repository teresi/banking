#!/usr/bin/env python3

"""
Test Parser.

Define a minimum implementation of Parser and test.
"""

import logging
import tempfile
import coloredlogs
import datetime
import os
from decimal import Decimal

import pytest
import pandas

from banking.parser import Parser
from banking.utils import file_dne_exc, TransactionColumns
from banking.test_utils import temp_file, temp_data

LOGGER = logging.getLogger(__name__)
coloredlogs.install(level=logging.DEBUG)


# MAGIC arbitrary values for testing
FAKE_TRANSACTIONS="""date,type,check,note,amount
01/01/2020,Credit,,LEGIT EMPLOYER,$+1000
01/02/2020,Debit,,ESTABLISHMENT STORE DEBIT CARD,($42)
02/01/2020,Deposit,,TRANSFER FROM,$+3.50,
02/03/2020,POS,,ESTABLISHMENT DEBIT PURCHASE,($3.50)"""


def _convert_amount(price):
    """Dollar to Decimal:$(X) for negatives, $+X for positives."""

    if price.startswith("($"):  # negative
        number = price[2:-1]  # remove ($...)
        return -1 * Decimal(number)
    elif price.startswith("$+"):  # positive
        number = price[2:]  # remove $+
        return +1 * Decimal(number)
    else:
        msg = "can't parse price, doesn't start with '($' or '$+': {}".format(price)
        logging.getLogger().error(msg)
        return None


def _convert_date(date_field):
    """Parse time into date, form of 01/31/1970"""

    date = datetime.datetime.strptime(str(date_field), "%m/%d/%Y").date()
    return date


class ParserImpl(Parser):
    """Implementation of a Parser for testing."""

    _MIN_DATE = datetime.date(1970, 1, 1)  # MAGIC arbirtrary

    INSTITUTION = "Totally Legit Bank"
    DELIMETER = ","
    _FIELD_2_TRANSACTION = {
        "date": TransactionColumns.DATE.name,
        "note": TransactionColumns.DESCRIPTION.name,
        "amount": TransactionColumns.AMOUNT.name,
    }
    _FIELD_NAMES = ["date", "amount", "note"]

    ACCOUNT = 8888  # MAGIC fake acount
    FILE_PREFIX_PART = "Acct_"  # MAGIC fake file formatting
    FILE_PREFIX = FILE_PREFIX_PART + str(ACCOUNT)

    @classmethod
    def field_names(cls):
        """The header values."""

        return [key for key in cls._FIELD_2_TRANSACTION.keys()]

    @classmethod
    def field_2_transaction(cls):
        """Header value to standardized names."""

        return cls._FIELD_2_TRANSACTION

    @classmethod
    def is_date_valid(cls, start, stop):
        """True if the dates found are valid for this parser."""

        return start >= cls._MIN_DATE

    def parse(self):
        """The data frame with our standard column naming convention."""

        return super().parse()

    def panda_frame(self):
        """Parse, but return the panda frame."""

        frame = self.parse_textfile(
            header_index=0,
            header_to_converter=self.COL_2_CONVERTER
        )
        return frame

    @classmethod
    def _check_filename(cls, filepath):
        """False if the filename is unexpected for this parser."""

        account_header = cls.FILE_PREFIX
        file_name = os.path.basename(filepath)
        matched = account_header in file_name
        if not matched:
            logging.debug("{} is invalid for {}".format(file_name, cls.__name__))
        return matched

    @property
    def COL_2_CONVERTER(cls):
        """Map column name to function to parse the value."""

        _col2convert = {
            "date": _convert_date,
            "amount": _convert_amount
        }
        return _col2convert

    @classmethod
    def check_header(cls, filepath, header=None, row=0, delim=','):
        """True if all the expected field names are in the header.

        Used to select a parser for an input file based on the header contents.

        Args:
            filepath(str): path to input data file
            header(str): header line, read file if None
            row(int): row index of the header line (zero based)
            delim(str): char delimiter
        Returns:
            (bool): true if header has all the expected fields
        """

        if row < 0:
            raise ValueError("row index of %i is < 0" % row)

        if header is None:
            line = [l for l in cls.yield_header(filepath, rows=row)][row]
        else:
            line = str(header).split(delim)

        # BUG multiline header not handled!
        matched = all([h in line for h in cls.field_names()])
        return matched

    @classmethod
    def is_file_parsable(cls, filepath, beginning=None):
        """True if this parser can decode the input file.

        Used to select a parser for an input file based on the filepath and header.

        Args:
            filepath(str): path to input data
            beginning(str):  first few lines of the raw data, skip reading file if not None
        Raises:
            FileNotFoundError: file does not exist
            IOError: file not readable or etc.
        """

        if not os.path.isfile(filepath):
            raise file_dne_exc(filepath)

        if not cls._check_filename(filepath):
            return False

        # BUG splitting multiple lines not tested & no input arg for header row!
        if beginning is not None:
            beginning = beginning.split('\n')[0]

        return cls.check_header(filepath, beginning)


@pytest.fixture
def temp_valid_input_file():

    with temp_data(
        prefix=ParserImpl.FILE_PREFIX,
        suffix='.csv',
        data=FAKE_TRANSACTIONS) as file_name:

        yield file_name


@pytest.fixture
def parser(temp_valid_input_file):
    """Yield a parser from the fake input file."""

    parser = ParserImpl(temp_valid_input_file)
    yield parser


@pytest.fixture
def frame(parser):
    """Yield a data frame after parsing the fake input file."""

    yield parser.parse()


def test_subclass_gen():
    """Can we iterate over the sub classes?"""

    classes = [klass for name, klass in ParserImpl.gen_implementations()]
    assert len(classes) >= 1  # MAGIC we've at least provided ParserImpl
    assert ParserImpl in classes


def test_subclass_is_registered(temp_file):
    """Does the sub class get registered?"""

    assert ParserImpl.__name__ in Parser._SUBCLASSES
    assert ParserImpl in Parser._SUBCLASSES.values()


def test_init_raise_file_no_exist():
    """Does init raise if file does not exist?"""

    with pytest.raises(FileNotFoundError):
        ParserImpl("/this/filepath/does/not/exist/really")


def test_check_header_read_file():
    """Is a good header accepted?"""

    data = ",".join(ParserImpl.field_names())
    with temp_data(prefix=ParserImpl.FILE_PREFIX, suffix=".csv", data=data) as file:
        assert ParserImpl.check_header(file, header=data, row=0) == True
        assert ParserImpl.is_file_parsable(file) == True


def test_is_parsable_bad_contents():
    """Is a file with bad header contents rejected?"""

    data = "this,is,the,wrong,header"
    with temp_data(prefix=None, suffix=".csv", data=data) as file:
        assert ParserImpl.check_header(file, row=0) == False
        assert ParserImpl.is_file_parsable(file) == False


def test_is_parsable_bad_filename():
    """Is a bad filename rejected?"""

    with temp_data(prefix="invalid_prefix") as file:
        assert ParserImpl.is_file_parsable(file) == False


def test_is_parsable_good_header():
    """Is a file with a good filename and header accepted?"""

    data = ",".join(ParserImpl.field_names())
    with temp_data(prefix=ParserImpl.FILE_PREFIX, suffix=".csv", data=data) as file:
        assert ParserImpl.is_file_parsable(file) == True


def test_parse_text_frame_rows(parser):
    """Does the frame read give the right number of transactions?"""

    # MAGIC our fake data has the first row as the header
    frame = parser.parse_textfile(header_index=0)
    # MAGIC -1 for the header
    n_transactions = len(FAKE_TRANSACTIONS.split('\n')) - 1
    rows, cols = frame.shape
    assert n_transactions == rows


def test_parse_text_frame_sum(parser):
    """Does the column converter work for the price?"""

    frame = parser.panda_frame()
    total = frame['amount'].sum()
    assert total == 1000-42  # MAGIC from our FAKE_TRANSACTIONS above


def test_parse_text_frame_dates(parser):
    """Does the column converter work for dates?"""

    frame = parser.panda_frame()
    expected = [
        datetime.date(2020,1,1),
        datetime.date(2020,1,2),
        datetime.date(2020,2,1),
        datetime.date(2020,2,3)
    ]
    for parsed, expected in zip(frame['date'], expected):
        assert parsed == expected


def test_remap_cols():
    """Are the column names remapped?"""

    input_keys = [k for k in ParserImpl.field_2_transaction().keys()]
    input_data = {k: [i] for i,k in enumerate(input_keys)}
    input_frame = pandas.DataFrame.from_dict(input_data)
    mapped_frame = ParserImpl.remap_cols(input_frame)
    mapped_keys = [c for c in mapped_frame.columns]
    for _in, _out in zip(input_keys, mapped_keys):
        assert all(input_frame[_in] == mapped_frame[_out])


def test_remap_populated(parser):
    """Are all the missing columns added after a remap?"""

    input_frame = parser.panda_frame()
    mapped_frame = parser.remap_cols(input_frame)
    mapped_cols = [c for c in mapped_frame.columns]
    for expected_col in TransactionColumns.names():
        assert expected_col in mapped_cols


def test_parse_sum(parser):
    """Does the `parse` function return the right amount?"""

    frame = parser.parse()
    total = frame[TransactionColumns.AMOUNT.name].sum()
    assert total == 1000-42


def test_parse_reject():
    """Does the `parse` function reject a bad file?"""

    with pytest.raises(ValueError):
        data = "this,is,the,wrong,header"
        with temp_data(prefix=None, suffix=".csv", data=data) as file:
            parser = ParserImpl(file)
            parser.parse()


def test_fill_bank(parser):
    """Does the bank name get populated?"""

    frame = parser.parse()
    assert all(frame[TransactionColumns.BANK.name] == parser.INSTITUTION)


def test_fill_account(parser):
    """Does the bank account get populated?"""

    frame = parser.parse()
    assert all(frame[TransactionColumns.ACCOUNT.name] == parser.ACCOUNT)


if __name__ == "__main__":
    pytest.main(['-s', __file__])  # for convenience
