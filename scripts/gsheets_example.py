#!/usr/bin/env python3

import httplib2
import os

# pip install google-auth-httplib2
# pip install google-api-python-client
from apiclient import discovery
from google.oauth2 import service_account

try:
    scopes = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/spreadsheets"]
    secret_file = os.path.join('/home/teresi/Downloads/banking-486b10311b6b.json')

    spreadsheet_id = '1h4PeQaOrc6FJY_PGoF1VGVFoqrUgCZKdVDsPvhkl92s'
    range_name = 'Sheet1!A1:D2'

    credentials = service_account.Credentials.from_service_account_file(secret_file, scopes=scopes)
    service = discovery.build('sheets', 'v4', credentials=credentials)

    values = [
        ['a1', 'b1', 'c1', 123],
        ['a2', 'b2', 'c2', 456],
    ]

    data = {
        'values' : values
    }

    service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, body=data, range=range_name, valueInputOption='USER_ENTERED').execute()



except OSError as e:
    print(e)
