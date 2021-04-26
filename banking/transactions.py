
"""
Wrapper for a frame of banking transactions.
"""

import os

import pandas as pd

from banking.utils import TransactionColumns

# FUTURE can we define the properties with a metaclass?
class Transactions:

    def __init__(self, frame, filepath):
        """

        Args:
            
        """

        self.path = str(filepath)
        self.frame = frame
        # TODO validate input frame (are the columns present?)

    @property
    def date(self):

        return self.frame[TransactionColumns.Date.name]

    @property
    def check_no(self):

        return self.frame[TransactionColumns.CHECK_NO.name]

    @property
    def amount(self):

        return self.frame[TransactionColumns.AMOUNT.name]

    @property
    def description(self):

        return self.frame[TransactionColumns.DESCRIPTION.name]

    @property
    def bank(self):

        return self.frame[TransactionColumns.BANK.name]

    @property
    def account(self):

        return self.frame[TransactionColumns.ACCOUNT.name]

    @property
    def category(self):

        return self.frame[TransactionColumns.CATEGORY.name]

    @property
    def POSTED_BALANCE(self):

        return self.frame[TransactionColumns.POSTED_BALANCE.name]

