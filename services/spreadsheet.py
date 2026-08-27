import os
import json
import logging

import gspread

from oauth2client.service_account import ServiceAccountCredentials

from config.settings import SPREADSHEET_ID


logger = logging.getLogger(__name__)


# =========================================================
# GOOGLE SHEET CONNECTION
# =========================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


# =========================================================
# GOOGLE CREDENTIALS
# =========================================================

google_credentials_raw = os.getenv(
    "GOOGLE_CREDENTIALS"
)


if not google_credentials_raw:

    raise RuntimeError(
        "GOOGLE_CREDENTIALS belum diset di "
        "Environment Variables hosting."
    )


try:

    google_credentials = json.loads(
        google_credentials_raw
    )

except json.JSONDecodeError as exc:

    raise RuntimeError(
        "GOOGLE_CREDENTIALS bukan JSON yang valid."
    ) from exc


# =========================================================
# GOOGLE AUTH
# =========================================================

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    google_credentials,
    scope,
)


client = gspread.authorize(
    creds
)


# =========================================================
# OPEN SPREADSHEET
# =========================================================

if not SPREADSHEET_ID:

    raise RuntimeError(
        "SPREADSHEET_ID belum diset di "
        "Environment Variables."
    )


sheet = client.open_by_key(
    SPREADSHEET_ID
).sheet1


logger.info(
    "Google Sheets connection berhasil."
)


# =========================================================
# GET MEMBERS
# =========================================================

def get_members():

    return sheet.get_all_records()
