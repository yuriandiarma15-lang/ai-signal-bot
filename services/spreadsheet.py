import os
import json

import gspread

from oauth2client.service_account import ServiceAccountCredentials


from config.settings import SPREADSHEET_ID





# ==========================
# GOOGLE SHEET CONNECTION
# ==========================


scope = [

    "https://spreadsheets.google.com/feeds",

    "https://www.googleapis.com/auth/drive"

]





google_credentials = json.loads(

    os.getenv(
        "GOOGLE_CREDENTIALS"
    )

)





creds = ServiceAccountCredentials.from_json_keyfile_dict(

    google_credentials,

    scope

)





client = gspread.authorize(

    creds

)





sheet = client.open_by_key(

    SPREADSHEET_ID

).sheet1







# ==========================
# GET MEMBERS
# ==========================


def get_members():


    return sheet.get_all_records()
