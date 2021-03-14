#!/usr/bin/env python3

from enum import Enum, unique
import httplib2
import os

from apiclient import discovery
from google.oauth2 import service_account

"""
Client to read / write to Google Sheets.

NOTE developed on Google Sheets API v4
NOTE requires (pip): google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""


@unique
class OAuthScopes(Enum):

    DRIVE_RWX = "https://www.googleapis.com/auth/drive"  # rwx files
    DRIVE_DRWX = "https://www.googleapis.com/auth/drive.file"  # rwx files + folders
    DRIVE_FETCH = "https://www.googleapis.com/auth/drive.readonly"  # download files
    SHEETS_RWX = "https://www.googleapis.com/auth/spreadsheets"  # rwx sheets
    SHEETS_R = "https://www.googleapis.com/auth/spreadsheets.readonly"  # read sheets


class Sheet:
    """Wraps a Google Sheet"""

    def __init__(
        self, spreadsheet_id, secret_filepath, scopes=[OAuthScopes.SHEETS_RWX]
    ):

        # SEE https://bitbucket.org/HidemotoKisuwa/inserting-data-through-api/src/master/DataImporter.py
        # SEE https://github.com/googleapis/google-api-python-client
        self.sheet_id = str(spreadsheet_id)
        self.secret_file = os.path.abspath(secret_filepath)
        self.scopes = [s.value for s in scopes]

        self.credentials = service_account.Credentials.from_service_account_file(
            self.secret_file, scopes=self.scopes
        )
        self.service = discovery.build("sheets", "v4", credentials=self.credentials)

    def _hello_world(self):

        values = [
            ["hello", "world"],
            ["guten", "tag"],
        ]

        data = {"values": values}

        self.write("Sheet1", "B2:C4", data)

    def write(self, sheet_name, range_name, data):

        self.service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            body=data,
            range=sheet_name + "!" + range_name,
            valueInputOption="USER_ENTERED",
        ).execute()
