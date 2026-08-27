"""
config/settings.py

GLOBAL SETTINGS
XAU AI SIGNAL BOT
================

Semua konfigurasi utama bot.

Credential:
- Environment variable
- .env

ATURAN ENTRY SMC
----------------
1. Struktur utama menggunakan M5.
2. Entry precision menggunakan M1.
3. Jika terdapat zona valid di M1:
       -> gunakan zona M1.
4. Jika tidak terdapat zona valid di M1:
       -> fallback mencari zona valid di M5.
5. Entry harus berada pada area SMC:
       - Order Block
       - Fair Value Gap
       - zona SMC valid lainnya
6. Jangan mengejar harga.
7. Pending order timeout 20 menit.
8. Jika tidak tersentuh:
       -> EXPIRED
       -> SKIP
9. Radius zona maksimum 100 pips.
10. XAUUSD:
       1 pip = 0.1 price
       100 pips = 10.0 price.
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

def _env(
    name,
    default=""
):
    return os.getenv(
        name,
        default
    )


def _int_env(
    name,
    default
):
    try:

        return int(
            os.getenv(
                name,
                str(default)
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def _float_env(
    name,
    default
):
    try:

        return float(
            os.getenv(
                name,
                str(default)
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def _bool_env(
    name,
    default=True
):
    return (
        _env(
            name,
            "true" if default else "false"
        ).lower()
        in (
            "1",
            "true",
            "yes",
            "on",
        )
    )


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
# TELEGRAM MESSAGE
# =========================================================

TELEGRAM_PARSE_MODE = _env(
    "TELEGRAM_PARSE_MODE",
    "Markdown"
)


TELEGRAM_DISABLE_WEB_PAGE_PREVIEW = _bool_env(
    "TELEGRAM_DISABLE_WEB_PAGE_PREVIEW",
    True
)


# =========================================================
# TELEGRAM SIGNAL SENDER
# =========================================================
#
# Delay antar member.
#
# Default:
# 0.15 detik.
#
# Bisa diubah melalui .env.
# =========================================================

SIGNAL_SEND_DELAY = _float_env(
    "SIGNAL_SEND_DELAY",
    0.15
)


# =========================================================
# TELEGRAM RETRY
# =========================================================

TELEGRAM_RETRY_COUNT = _int_env(
    "TELEGRAM_RETRY_COUNT",
    3
)


TELEGRAM_RETRY_DELAY = _float_env(
    "TELEGRAM_RETRY_DELAY",
    2
)


# =========================================================
# SIGNAL DETAIL
# =========================================================

SIGNAL_DETAIL_ENABLED = _bool_env(
    "SIGNAL_DETAIL_ENABLED",
    True
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
# ENTRY TIMEFRAME PRIORITY
# =========================================================
#
# M1 > M5
#
# 1. Cari zona M1.
# 2. Jika tidak ada -> M5.
# 3. Jika tidak ada -> NO TRADE.
# =========================================================

SMC_ENTRY_PRIORITY = _env(
    "SMC_ENTRY_PRIORITY",
    "M1>M5"
)


SMC_ALLOW_M1_ENTRY = _bool_env(
    "SMC_ALLOW_M1_ENTRY",
    True
)


SMC_ALLOW_M5_ENTRY = _bool_env(
    "SMC_ALLOW_M5_ENTRY",
    True
)


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


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

CANDLES_FOR_STRUCTURE = SMC_CANDLES_FOR_STRUCTURE


CANDLES_LOOKBACK = SMC_CANDLES_LOOKBACK


CANDLES_ENTRY_LOOKBACK = SMC_CANDLES_ENTRY_LOOKBACK


# =========================================================
# RISK MANAGEMENT
# =========================================================
#
# XAUUSD:
#
# 1 pip = 0.1 price
#
# SL  = 50 pips  = 5.0 price
# TP1 = 70 pips  = 7.0 price
# TP2 = 150 pips = 15.0 price
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


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

SL_DISTANCE = SMC_SL_DISTANCE


TP1_DISTANCE = SMC_TP1_DISTANCE


TP2_DISTANCE = SMC_TP2_DISTANCE


SL_PIPS = SMC_SL_PIPS


TP1_PIPS = SMC_TP1_PIPS


TP2_PIPS = SMC_TP2_PIPS


# =========================================================
# ENTRY TOLERANCE
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
#
# Default:
#
# 100 pips
#
# XAU:
#
# 100 × 0.1 = 10.0 price
# =========================================================

SMC_MAX_ZONE_DISTANCE_PIPS = _float_env(
    "SMC_MAX_ZONE_DISTANCE_PIPS",
    100
)


SMC_MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE_PIPS
    * SMC_PIP_VALUE
)


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE
)


MAX_ZONE_DISTANCE_PIPS = (
    SMC_MAX_ZONE_DISTANCE_PIPS
)


# =========================================================
# ZONE VALIDATION
# =========================================================

SMC_ZONE_TOUCH_LOOKBACK = _int_env(
    "SMC_ZONE_TOUCH_LOOKBACK",
    10
)


SMC_MIN_ENTRY_CANDLES = _int_env(
    "SMC_MIN_ENTRY_CANDLES",
    10
)


SMC_REQUIRE_VALID_ZONE = _bool_env(
    "SMC_REQUIRE_VALID_ZONE",
    True
)


SMC_PREFER_FRESH_ZONE = _bool_env(
    "SMC_PREFER_FRESH_ZONE",
    True
)


SMC_ALLOW_MITIGATED_ZONE = _bool_env(
    "SMC_ALLOW_MITIGATED_ZONE",
    True
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


SMC_ENABLE_PENDING_ORDER = _bool_env(
    "SMC_ENABLE_PENDING_ORDER",
    True
)


# =========================================================
# MARKET ENTRY
# =========================================================

SMC_ENABLE_MARKET_ENTRY = _bool_env(
    "SMC_ENABLE_MARKET_ENTRY",
    True
)


SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET = _bool_env(
    "SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET",
    True
)


# =========================================================
# TIMEZONE
# =========================================================

TIMEZONE = _env(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta"
)


# =========================================================
# GOOGLE SHEETS
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

    # =====================================================
    # ASIA
    # =====================================================

    {
        "name": "Asia",

        "hours": list(
            range(
                7,
                15
            )
        ),

        "note": (
            "Pergerakan cenderung lebih tenang "
            "dan choppy, sehingga konfirmasi "
            "struktur perlu lebih ketat."
        ),
    },

    # =====================================================
    # LONDON
    # =====================================================

    {
        "name": "London",

        "hours": list(
            range(
                15,
                20
            )
        ),

        "note": (
            "Likuiditas mulai meningkat dan "
            "breakout struktur lebih sering "
            "terjadi pada XAUUSD."
        ),
    },

    # =====================================================
    # NEW YORK
    # =====================================================

    {
        "name": "New York",

        "hours": (
            list(
                range(
                    20,
                    24
                )
            )
            + [
                0,
                1,
                2,
            ]
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
    range(
        7,
        24
    )
)


ACTIVE_HOURS_EXTENDED = [
    0,
    1,
    2,
]


# =========================================================
# DAY OF WEEK
# =========================================================

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


MAX_SIGNAL_PER_DAY = _int_env(
    "MAX_SIGNAL_PER_DAY",
    20
)


# =========================================================
# PERFORMANCE CHANNEL
# =========================================================

PERFORMANCE_CHANNEL_ID = _int_env(
    "PERFORMANCE_CHANNEL_ID",
    0
)


# =========================================================
# =========================================================
# FUNDAMENTAL NEWS
# =========================================================
# =========================================================

FUNDAMENTAL_ENABLED = _bool_env(
    "FUNDAMENTAL_ENABLED",
    True
)


FUNDAMENTAL_INTERVAL_MINUTES = _int_env(
    "FUNDAMENTAL_INTERVAL_MINUTES",
    60
)


FUNDAMENTAL_NEWS_PER_UPDATE = _int_env(
    "FUNDAMENTAL_NEWS_PER_UPDATE",
    1
)


FUNDAMENTAL_MAX_NEWS_AGE_HOURS = _int_env(
    "FUNDAMENTAL_MAX_NEWS_AGE_HOURS",
    24
)


# =========================================================
# FUNDAMENTAL API
# =========================================================

NEWS_API_KEY = _env(
    "NEWS_API_KEY",
    ""
)


NEWS_API_URL = _env(
    "NEWS_API_URL",
    ""
)


NEWS_REQUEST_TIMEOUT = _int_env(
    "NEWS_REQUEST_TIMEOUT",
    15
)


# =========================================================
# NEWS LANGUAGE
# =========================================================

NEWS_SOURCE_LANGUAGE = _env(
    "NEWS_SOURCE_LANGUAGE",
    "en"
)


NEWS_OUTPUT_LANGUAGE = _env(
    "NEWS_OUTPUT_LANGUAGE",
    "id"
)


FUNDAMENTAL_LANGUAGE = _env(
    "FUNDAMENTAL_LANGUAGE",
    "id"
)


# =========================================================
# NEWS AGE
# =========================================================

NEWS_MAX_AGE_MINUTES = _int_env(
    "NEWS_MAX_AGE_MINUTES",
    180
)


# =========================================================
# NEWS FETCH
# =========================================================

NEWS_FETCH_LIMIT = _int_env(
    "NEWS_FETCH_LIMIT",
    10
)


# =========================================================
# NEWS KEYWORDS
# =========================================================

NEWS_KEYWORDS = [

    "gold",

    "XAUUSD",

    "XAU",

    "Federal Reserve",

    "Fed",

    "interest rate",

    "inflation",

    "CPI",

    "PCE",

    "NFP",

    "nonfarm payrolls",

    "unemployment",

    "USD",

    "US dollar",

    "Treasury yields",

    "bond yields",

    "geopolitical",

    "war",

    "Middle East",

]


# =========================================================
# FUNDAMENTAL SEARCH KEYWORDS
# =========================================================

FUNDAMENTAL_SEARCH_KEYWORDS = [

    "gold",

    "XAUUSD",

    "XAU/USD",

    "Federal Reserve",

    "Fed",

    "interest rate",

    "US dollar",

    "USD",

    "Treasury yields",

    "US yields",

    "inflation",

    "central bank",

    "monetary policy",

    "geopolitical",

    "gold price",

]


# =========================================================
# BLOCKED NEWS
# =========================================================
#
# Berita berikut tidak digunakan oleh modul
# Fundamental khusus.
# =========================================================

FUNDAMENTAL_BLOCKED_KEYWORDS = [

    "FOMC",

    "Federal Open Market Committee",

    "NFP",

    "Non-Farm Payroll",

    "Nonfarm Payroll",

    "Payrolls",

    "PPI",

    "Producer Price Index",

    "CPI",

    "Consumer Price Index",

]


# =========================================================
# SOURCE PRIORITY
# =========================================================

FUNDAMENTAL_SOURCE_PRIORITY = [

    "Reuters",

    "Bloomberg",

    "CNBC",

    "Wall Street Journal",

    "Financial Times",

    "Investing.com",

    "FXStreet",

]


# =========================================================
# SOURCE VALIDATION
# =========================================================

NEWS_REQUIRE_SOURCE = _bool_env(
    "NEWS_REQUIRE_SOURCE",
    True
)


NEWS_REQUIRE_URL = _bool_env(
    "NEWS_REQUIRE_URL",
    True
)


# =========================================================
# DUPLICATE PROTECTION
# =========================================================

NEWS_PREVENT_DUPLICATE = _bool_env(
    "NEWS_PREVENT_DUPLICATE",
    True
)


# =========================================================
# TRANSLATION
# =========================================================

NEWS_TRANSLATE_TO_INDONESIAN = _bool_env(
    "NEWS_TRANSLATE_TO_INDONESIAN",
    True
)


# =========================================================
# SUMMARY
# =========================================================

NEWS_ENABLE_SUMMARY = _bool_env(
    "NEWS_ENABLE_SUMMARY",
    True
)


# =========================================================
# GOLD IMPACT
# =========================================================

NEWS_ENABLE_GOLD_IMPACT = _bool_env(
    "NEWS_ENABLE_GOLD_IMPACT",
    True
)


# =========================================================
# COMBINATION
# =========================================================

NEWS_ENABLE_COMBINATION = _bool_env(
    "NEWS_ENABLE_COMBINATION",
    True
)


# =========================================================
# NEWS CHANNEL
# =========================================================

NEWS_CHANNEL_ID = _int_env(
    "NEWS_CHANNEL_ID",
    0
)


# =========================================================
# NEWS FAILURE POLICY
# =========================================================
#
# Jika news provider gagal:
#
# SMC signal utama tidak ikut gagal.
#
# Combined AI tetap tunduk pada:
# COMBINED_REQUIRE_FUNDAMENTAL
# =========================================================

NEWS_FAIL_SILENT = _bool_env(
    "NEWS_FAIL_SILENT",
    True
)


# =========================================================
# FUNDAMENTAL CACHE
# =========================================================

FUNDAMENTAL_NEWS_CACHE_FILE = _env(
    "FUNDAMENTAL_NEWS_CACHE_FILE",
    "data/fundamental_news.json"
)


# =========================================================
# =========================================================
# COMBINED AI
# =========================================================
# =========================================================

COMBINED_AI_ENABLED = _bool_env(
    "COMBINED_AI_ENABLED",
    True
)


COMBINED_AI_INTERVAL_MINUTES = _int_env(
    "COMBINED_AI_INTERVAL_MINUTES",
    90
)


COMBINED_NEWS_PER_UPDATE = _int_env(
    "COMBINED_NEWS_PER_UPDATE",
    1
)


COMBINED_MAX_NEWS_AGE_HOURS = _int_env(
    "COMBINED_MAX_NEWS_AGE_HOURS",
    24
)


# =========================================================
# COMBINED REQUIRE SMC
# =========================================================

COMBINED_REQUIRE_SMC = _bool_env(
    "COMBINED_REQUIRE_SMC",
    True
)


# =========================================================
# COMBINED REQUIRE FUNDAMENTAL
# =========================================================

COMBINED_REQUIRE_FUNDAMENTAL = _bool_env(
    "COMBINED_REQUIRE_FUNDAMENTAL",
    True
)


# =========================================================
# COMBINED RISK
# =========================================================

COMBINED_SL_PIPS = SMC_SL_PIPS


COMBINED_TP1_PIPS = SMC_TP1_PIPS


COMBINED_TP2_PIPS = SMC_TP2_PIPS


COMBINED_SL_DISTANCE = SMC_SL_DISTANCE


COMBINED_TP1_DISTANCE = SMC_TP1_DISTANCE


COMBINED_TP2_DISTANCE = SMC_TP2_DISTANCE


# =========================================================
# COMBINED CACHE
# =========================================================

COMBINED_NEWS_CACHE_FILE = _env(
    "COMBINED_NEWS_CACHE_FILE",
    "data/combined_news.json"
)


# =========================================================
# =========================================================
# AI
# =========================================================
# =========================================================

AI_ENABLED = _bool_env(
    "AI_ENABLED",
    True
)


AI_API_KEY = _env(
    "AI_API_KEY",
    ""
)


AI_MODEL = _env(
    "AI_MODEL",
    ""
)


AI_TIMEOUT = _int_env(
    "AI_TIMEOUT",
    30
)


# =========================================================
# DEBUG
# =========================================================

DEBUG_SMC = _bool_env(
    "DEBUG_SMC",
    False
)


DEBUG_NEWS = _bool_env(
    "DEBUG_NEWS",
    False
)


DEBUG_COMBINED = _bool_env(
    "DEBUG_COMBINED",
    False
)


# =========================================================
# SETTINGS VALIDATION
# =========================================================

def validate_settings():

    errors = []


    # =====================================================
    # REQUIRED CREDENTIALS
    # =====================================================

    if not BOT_TOKEN:

        errors.append(
            "BOT_TOKEN belum diisi."
        )


    if not TWELVE_TOKEN:

        errors.append(
            "TWELVE_TOKEN belum diisi."
        )


    if not SPREADSHEET_ID:

        errors.append(
            "SPREADSHEET_ID belum diisi."
        )


    # =====================================================
    # RISK
    # =====================================================

    if SMC_PIP_VALUE <= 0:

        errors.append(
            "SMC_PIP_VALUE harus lebih besar dari 0."
        )


    if SMC_SL_PIPS <= 0:

        errors.append(
            "SMC_SL_PIPS harus lebih besar dari 0."
        )


    if SMC_TP1_PIPS <= 0:

        errors.append(
            "SMC_TP1_PIPS harus lebih besar dari 0."
        )


    if SMC_TP2_PIPS <= 0:

        errors.append(
            "SMC_TP2_PIPS harus lebih besar dari 0."
        )


    # =====================================================
    # ZONE
    # =====================================================

    if SMC_MAX_ZONE_DISTANCE_PIPS <= 0:

        errors.append(
            "SMC_MAX_ZONE_DISTANCE_PIPS harus "
            "lebih besar dari 0."
        )


    # =====================================================
    # PENDING
    # =====================================================

    if SMC_PENDING_TIMEOUT_MINUTES <= 0:

        errors.append(
            "SMC_PENDING_TIMEOUT_MINUTES harus "
            "lebih besar dari 0."
        )


    # =====================================================
    # CANDLES
    # =====================================================

    if SMC_CANDLES_FOR_STRUCTURE < 3:

        errors.append(
            "SMC_CANDLES_FOR_STRUCTURE minimal 3."
        )


    if SMC_CANDLES_ENTRY_LOOKBACK < 1:

        errors.append(
            "SMC_CANDLES_ENTRY_LOOKBACK minimal 1."
        )


    # =====================================================
    # SEND
    # =====================================================

    if SIGNAL_SEND_DELAY < 0:

        errors.append(
            "SIGNAL_SEND_DELAY tidak boleh negatif."
        )


    if TELEGRAM_RETRY_COUNT < 0:

        errors.append(
            "TELEGRAM_RETRY_COUNT tidak boleh negatif."
        )


    if TELEGRAM_RETRY_DELAY < 0:

        errors.append(
            "TELEGRAM_RETRY_DELAY tidak boleh negatif."
        )


    # =====================================================
    # NEWS
    # =====================================================

    if FUNDAMENTAL_INTERVAL_MINUTES <= 0:

        errors.append(
            "FUNDAMENTAL_INTERVAL_MINUTES harus "
            "lebih besar dari 0."
        )


    if COMBINED_AI_INTERVAL_MINUTES <= 0:

        errors.append(
            "COMBINED_AI_INTERVAL_MINUTES harus "
            "lebih besar dari 0."
        )


    if NEWS_REQUEST_TIMEOUT <= 0:

        errors.append(
            "NEWS_REQUEST_TIMEOUT harus "
            "lebih besar dari 0."
        )


    # =====================================================
    # NEWS LIMIT
    # =====================================================

    if NEWS_FETCH_LIMIT < 1:

        errors.append(
            "NEWS_FETCH_LIMIT minimal 1."
        )


    if FUNDAMENTAL_NEWS_PER_UPDATE < 1:

        errors.append(
            "FUNDAMENTAL_NEWS_PER_UPDATE minimal 1."
        )


    if COMBINED_NEWS_PER_UPDATE < 1:

        errors.append(
            "COMBINED_NEWS_PER_UPDATE minimal 1."
        )


    # =====================================================
    # ERROR
    # =====================================================

    if errors:

        raise ValueError(
            "Konfigurasi settings tidak valid:\n- "
            + "\n- ".join(errors)
        )


    return True
