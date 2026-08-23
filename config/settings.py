"""
GLOBAL SETTINGS
XAU AI SIGNAL BOT

Semua konfigurasi utama bot.

Credential diambil dari environment variable / .env
"""

import os

from dotenv import load_dotenv


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()


# =========================================================
# HELPER
# =========================================================

def _env(name, default=""):
    return os.getenv(name, default)


def _int_env(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _float_env(name, default):
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


# =========================================================
# TELEGRAM
# =========================================================

BOT_TOKEN = _env(
    "BOT_TOKEN",
    ""
)


SOURCE_GROUP_ID = _int_env(
    "SOURCE_GROUP_ID",
    0
)


# =========================================================
# TWELVE DATA
# =========================================================

TWELVE_TOKEN = _env(
    "TWELVE_TOKEN",
    ""
)

# =========================================================
# BACKWARD COMPATIBILITY
#
# File lama menggunakan:
# TWELVEDATA_API_KEY
#
# Jadi diarahkan ke TWELVE_TOKEN.
# =========================================================

TWELVEDATA_API_KEY = TWELVE_TOKEN


# =========================================================
# MARKET
# =========================================================

SMC_SYMBOL = _env(
    "SMC_SYMBOL",
    "XAU/USD"
)


SYMBOL = SMC_SYMBOL


# =========================================================
# TIMEFRAME
# =========================================================

SMC_TF_STRUCTURE = _env(
    "SMC_TF_STRUCTURE",
    "5min"
)


SMC_TF_ENTRY = _env(
    "SMC_TF_ENTRY",
    "1min"
)


TF_STRUCTURE = SMC_TF_STRUCTURE

TF_ENTRY = SMC_TF_ENTRY


# =========================================================
# CANDLE SETTINGS
# =========================================================

SMC_CANDLES_FOR_STRUCTURE = _int_env(
    "SMC_CANDLES_FOR_STRUCTURE",
    12
)


SMC_CANDLES_LOOKBACK = _int_env(
    "SMC_CANDLES_LOOKBACK",
    60
)


SMC_CANDLES_ENTRY_LOOKBACK = _int_env(
    "SMC_CANDLES_ENTRY_LOOKBACK",
    30
)


# Backward compatibility

CANDLES_FOR_STRUCTURE = (
    SMC_CANDLES_FOR_STRUCTURE
)

CANDLES_LOOKBACK = (
    SMC_CANDLES_LOOKBACK
)

CANDLES_ENTRY_LOOKBACK = (
    SMC_CANDLES_ENTRY_LOOKBACK
)


# =========================================================
# RISK MANAGEMENT
# =========================================================

SMC_PIP_VALUE = _float_env(
    "SMC_PIP_VALUE",
    0.1
)


SMC_SL_PIPS = _float_env(
    "SMC_SL_PIPS",
    50
)


SMC_TP1_PIPS = _float_env(
    "SMC_TP1_PIPS",
    70
)


SMC_TP2_PIPS = _float_env(
    "SMC_TP2_PIPS",
    150
)


# =========================================================
# PRICE DISTANCE
# =========================================================

SMC_SL_DISTANCE = (
    SMC_SL_PIPS
    * SMC_PIP_VALUE
)


SMC_TP1_DISTANCE = (
    SMC_TP1_PIPS
    * SMC_PIP_VALUE
)


SMC_TP2_DISTANCE = (
    SMC_TP2_PIPS
    * SMC_PIP_VALUE
)


# Backward compatibility

SL_DISTANCE = SMC_SL_DISTANCE

TP1_DISTANCE = SMC_TP1_DISTANCE

TP2_DISTANCE = SMC_TP2_DISTANCE

SL_PIPS = SMC_SL_PIPS

TP1_PIPS = SMC_TP1_PIPS

TP2_PIPS = SMC_TP2_PIPS


# =========================================================
# ENTRY
# =========================================================

SMC_MARKET_ENTRY_TOLERANCE = _float_env(
    "SMC_MARKET_ENTRY_TOLERANCE",
    0.3
)


MARKET_ENTRY_TOLERANCE = (
    SMC_MARKET_ENTRY_TOLERANCE
)


# =========================================================
# MAX ZONE DISTANCE
# =========================================================

SMC_MAX_ZONE_DISTANCE = _float_env(
    "SMC_MAX_ZONE_DISTANCE",
    SMC_SL_DISTANCE * 1.5
)


MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE
)


# =========================================================
# ZONE TOUCH
# =========================================================

SMC_ZONE_TOUCH_LOOKBACK = _int_env(
    "SMC_ZONE_TOUCH_LOOKBACK",
    10
)


SMC_MIN_ENTRY_CANDLES = _int_env(
    "SMC_MIN_ENTRY_CANDLES",
    10
)


# =========================================================
# PENDING ORDER
# =========================================================

SMC_PENDING_TIMEOUT_MINUTES = _int_env(
    "SMC_PENDING_TIMEOUT_MINUTES",
    20
)


PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# =========================================================
# TIMEZONE
# =========================================================

TIMEZONE = _env(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta"
)


# =========================================================
# GOOGLE SHEET
# =========================================================

SPREADSHEET_ID = _env(
    "SPREADSHEET_ID",
    ""
)


DATA_SHEET_NAME = _env(
    "DATA_SHEET_NAME",
    "data"
)


TRIAL_SHEET_NAME = _env(
    "TRIAL_SHEET_NAME",
    "TRIAL"
)


GOOGLE_CREDENTIALS = _env(
    "GOOGLE_CREDENTIALS",
    ""
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_USERNAME = _env(
    "ADMIN_USERNAME",
    ""
)


# =========================================================
# RENEW
# =========================================================

RENEW_BOT = _env(
    "RENEW_BOT",
    ""
)


# =========================================================
# WEBSITE
# =========================================================

WEBSITE_URL = _env(
    "WEBSITE_URL",
    ""
)


API_KEY = _env(
    "API_KEY",
    ""
)


# =========================================================
# SIGNAL
# =========================================================

SIGNAL_NAME = _env(
    "SIGNAL_NAME",
    "XAU AI INTELLIGENCE"
)


# =========================================================
# SESSION
# =========================================================

SESSIONS = [

    {
        "name": "Asia",

        "hours": list(
            range(7, 15)
        ),

        "note": (
            "Pergerakan cenderung lebih tenang "
            "dan choppy, sehingga konfirmasi "
            "struktur perlu lebih ketat."
        ),
    },

    {
        "name": "London",

        "hours": list(
            range(15, 20)
        ),

        "note": (
            "Likuiditas mulai meningkat dan "
            "breakout struktur lebih sering "
            "terjadi pada XAUUSD."
        ),
    },

    {
        "name": "New York",

        "hours": (
            list(range(20, 24))
            + [0, 1, 2]
        ),

        "note": (
            "Likuiditas dan volatilitas biasanya "
            "tinggi, sehingga perlu waspada "
            "spike dan berita fundamental."
        ),
    },

]


# =========================================================
# MARKET SESSION SCHEDULE
# =========================================================

ACTIVE_HOURS_MAIN = list(
    range(7, 24)
)


ACTIVE_HOURS_EXTENDED = [
    0,
    1,
    2,
]


DOW_MAIN = (
    "mon,tue,wed,thu,fri"
)


DOW_EXTENDED = (
    "tue,wed,thu,fri,sat"
)


# =========================================================
# MESSAGE
# =========================================================

MAX_MESSAGE_WIDTH = _int_env(
    "MAX_MESSAGE_WIDTH",
    34
)


# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = _env(
    "LOG_LEVEL",
    "INFO"
).upper()


# =========================================================
# TRIAL
# =========================================================

TRIAL_MINUTES = _int_env(
    "TRIAL_MINUTES",
    30
)


# =========================================================
# KICK / EXPIRE
# =========================================================

KICK_DELAY_MINUTES = _int_env(
    "KICK_DELAY_MINUTES",
    2
)


# =========================================================
# SIGNAL HISTORY
# =========================================================

MAX_SIGNAL_HISTORY = _int_env(
    "MAX_SIGNAL_HISTORY",
    100
)


# =========================================================
# SIGNAL LIMIT
# =========================================================

MAX_SIGNAL_PER_DAY = _int_env(
    "MAX_SIGNAL_PER_DAY",
    20
)


# =========================================================
# DEBUG
# =========================================================

DEBUG_SMC = (
    _env(
        "DEBUG_SMC",
        "false"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)
