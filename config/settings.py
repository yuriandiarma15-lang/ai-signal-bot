import os
from dotenv import load_dotenv

load_dotenv()


# ==========================
# TELEGRAM BOT
# ==========================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


# ==========================
# MARKET DATA
# ==========================

TWELVE_TOKEN = os.getenv(
    "TWELVE_TOKEN"
)


# ==========================
# TELEGRAM GROUP / CHANNEL
# ==========================

SOURCE_GROUP_ID = int(
    os.getenv(
        "SOURCE_GROUP_ID",
        "0"
    )
)


# ==========================
# GOOGLE SHEET (JIKA DIPAKAI)
# ==========================

SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID"
)


# ==========================
# ADMIN
# ==========================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)


# ==========================
# RENEW SYSTEM
# ==========================

RENEW_BOT = os.getenv(
    "RENEW_BOT"
)


# ==========================
# TIMEZONE
# ==========================

TIMEZONE = os.getenv(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta"
)



# ==========================
# WEBSITE API
# ==========================

WEBSITE_URL = os.getenv(
    "WEBSITE_URL"
)


API_KEY = os.getenv(
    "API_KEY"
)
