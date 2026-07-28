import os

from dotenv import load_dotenv


load_dotenv()



BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)



TWELVE_TOKEN = os.getenv(
    "TWELVE_TOKEN"
)



SOURCE_GROUP_ID = int(
    os.getenv(
        "SOURCE_GROUP_ID"
    )
)



SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID"
)



ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)



RENEW_BOT = os.getenv(
    "RENEW_BOT"
)



TIMEZONE = os.getenv(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta"
)
