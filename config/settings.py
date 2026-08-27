"""
config/settings.py

GLOBAL SETTINGS
XAU AI SIGNAL BOT
================

Semua konfigurasi utama bot.

Credential:
    environment variable / .env

ATURAN ENTRY SMC
----------------
1. Struktur utama menggunakan M5.
2. Entry precision menggunakan M1.
3. Prioritas zona:
       M1 -> M5
4. Entry wajib berada pada zona SMC valid.
5. Jangan mengejar harga.
6. Pending order timeout 20 menit.
7. Zona di luar radius maksimum tidak digunakan.
8. XAUUSD:
       1 pip = 0.1 price

Risk:
    SL  = 50 pips
    TP1 = 70 pips
    TP2 = 150 pips
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
        return int(
            os.getenv(
                name,
                str(default)
            )
        )
    except (TypeError, ValueError):
        return default


def _float_env(name, default):
    try:
        return float(
            os.getenv(
                name,
                str(default)
            )
        )
    except (TypeError, ValueError):
        return default


def _bool_env(name, default=True):
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
# TELEGRAM SENDER
# =========================================================

# Delay antar member.
#
# 0.15 detik cukup ringan untuk pengiriman massal.
#
TELEGRAM_SEND_DELAY = _float_env(
    "TELEGRAM_SEND_DELAY",
    0.15
)


# Backward compatibility
SEND_DELAY = TELEGRAM_SEND_DELAY


# Parse mode utama signal.
#
# Markdown dipertahankan karena format signal lama
# menggunakan Markdown.
#
TELEGRAM_PARSE_MODE = _env(
    "TELEGRAM_PARSE_MODE",
    "Markdown"
)


PARSE_MODE = TELEGRAM_PARSE_MODE


# Retry pengiriman Telegram.
#
TELEGRAM_SEND_RETRY_COUNT = _int_env(
    "TELEGRAM_SEND_RETRY_COUNT",
    3
)


TELEGRAM_SEND_RETRY_DELAY = _float_env(
    "TELEGRAM_SEND_RETRY_DELAY",
    2
)


# =========================================================
# GOOGLE SHEETS MEMBER RETRY
# =========================================================

MEMBER_RETRY_COUNT = _int_env(
    "MEMBER_RETRY_COUNT",
    3
)


MEMBER_RETRY_DELAY = _float_env(
    "MEMBER_RETRY_DELAY",
    2
)


# =========================================================
# TWELVE DATA
# =========================================================

TWELVE_TOKEN = _env(
    "TWELVE_TOKEN",
    ""
)


# Backward compatibility
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

# Manual /signal
#
# 12 candle M5 CLOSED
# = 60 menit struktur
#
SMC_CANDLES_FOR_STRUCTURE = _int_env(
    "SMC_CANDLES_FOR_STRUCTURE",
    12
)


# Scheduler
SMC_CANDLES_LOOKBACK = _int_env(
    "SMC_CANDLES_LOOKBACK",
    60
)


# Entry timeframe
#
# Default:
# 30 candle M1
#
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

# XAUUSD:
#
# 1 pip = 0.1 price
#
SMC_PIP_VALUE = _float_env(
    "SMC_PIP_VALUE",
    0.1
)


# =========================================================
# STOP LOSS
# =========================================================

SMC_SL_PIPS = _float_env(
    "SMC_SL_PIPS",
    50
)


# =========================================================
# TAKE PROFIT 1
# =========================================================

SMC_TP1_PIPS = _float_env(
    "SMC_TP1_PIPS",
    70
)


# =========================================================
# TAKE PROFIT 2
# =========================================================

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
# MARKET ENTRY
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
# XAUUSD:
#
# 100 pips = 10.0 price
#
SMC_MAX_ZONE_DISTANCE_PIPS = _float_env(
    "SMC_MAX_ZONE_DISTANCE_PIPS",
    100
)


SMC_MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE_PIPS
    * SMC_PIP_VALUE
)


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
# M1 CONFIRMATION
# =========================================================

SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET = _bool_env(
    "SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET",
    True
)


# =========================================================
# MARKET / PENDING ENTRY
# =========================================================

SMC_ENABLE_PENDING_ORDER = _bool_env(
    "SMC_ENABLE_PENDING_ORDER",
    True
)


SMC_ENABLE_MARKET_ENTRY = _bool_env(
    "SMC_ENABLE_MARKET_ENTRY",
    True
)


# =========================================================
# PENDING ORDER
# =========================================================
#
# Pending order:
#
# valid selama 20 menit.
#
SMC_PENDING_TIMEOUT_MINUTES = _int_env(
    "SMC_PENDING_TIMEOUT_MINUTES",
    20
)


PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# =========================================================
# PENDING SIGNAL MONITOR
# =========================================================

PENDING_MONITOR_ENABLED = _bool_env(
    "PENDING_MONITOR_ENABLED",
    True
)


PENDING_MONITOR_INTERVAL_SECONDS = _int_env(
    "PENDING_MONITOR_INTERVAL_SECONDS",
    30
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
# SIGNAL DETAIL
# =========================================================

SIGNAL_DETAIL_ENABLED = _bool_env(
    "SIGNAL_DETAIL_ENABLED",
    True
)


SIGNAL_DETAIL_BUTTON_TEXT = _env(
    "SIGNAL_DETAIL_BUTTON_TEXT",
    "📊 Detail Analisa"
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
# SESSION
# =========================================================

SESSIONS = [

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
# PERFORMANCE CHANNEL
# =========================================================

PERFORMANCE_CHANNEL_ID = _int_env(
    "PERFORMANCE_CHANNEL_ID",
    0
)


# =========================================================
# FUNDAMENTAL ACCESS
# =========================================================
#
# Fundamental:
#
# 6 Bulan
# 12 Bulan
# Lifetime
#
# Tidak:
#
# 1 Bulan
# MITRA HFM
#
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


# =====================================================
# FIX: Sebelumnya 24 jam.
#
# Dari log produksi, banyak berita finansial yang
# RELEVAN (Fed, Treasury, national debt) hanya
# meleset tipis (24-25 jam) dari batas lama, sehingga
# selalu ditolak TOO_OLD dan command /fundamental
# jadi sering kosong.
#
# Dilonggarkan ke 36 jam supaya tidak terlalu ketat,
# tapi tetap menolak berita yang benar-benar basi.
# =====================================================

FUNDAMENTAL_MAX_NEWS_AGE_HOURS = _int_env(
    "FUNDAMENTAL_MAX_NEWS_AGE_HOURS",
    36
)


# =========================================================
# FUNDAMENTAL SEARCH
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
# FUNDAMENTAL SOURCE
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
# FUNDAMENTAL LANGUAGE
# =========================================================

FUNDAMENTAL_LANGUAGE = _env(
    "FUNDAMENTAL_LANGUAGE",
    "id"
)


# =========================================================
# NEWS API
# =========================================================

NEWS_API_KEY = _env(
    "NEWS_API_KEY",
    ""
)


NEWS_API_URL = _env(
    "NEWS_API_URL",
    ""
)


NEWS_SOURCE_LANGUAGE = _env(
    "NEWS_SOURCE_LANGUAGE",
    "en"
)


NEWS_OUTPUT_LANGUAGE = _env(
    "NEWS_OUTPUT_LANGUAGE",
    "id"
)


# =========================================================
# LEGACY NEWS SYSTEM
# =========================================================

FUNDAMENTAL_NEWS_ENABLED = _bool_env(
    "FUNDAMENTAL_NEWS_ENABLED",
    True
)


FUNDAMENTAL_NEWS_INTERVAL_MINUTES = _int_env(
    "FUNDAMENTAL_NEWS_INTERVAL_MINUTES",
    60
)


COMBINATION_NEWS_ENABLED = _bool_env(
    "COMBINATION_NEWS_ENABLED",
    True
)


COMBINATION_NEWS_INTERVAL_MINUTES = _int_env(
    "COMBINATION_NEWS_INTERVAL_MINUTES",
    90
)


NEWS_MAX_AGE_MINUTES = _int_env(
    "NEWS_MAX_AGE_MINUTES",
    180
)


# =====================================================
# FIX: Sebelumnya 10.
#
# Dengan pageSize=10 ke NewsAPI, query OR yang berisi
# banyak keyword umum ("gold OR ... OR USD OR Fed ...")
# sering "kehabisan slot" duluan oleh artikel yang
# tidak relevan (mis. rilis paket PyPI yang kebetulan
# menyebut kata umum).
#
# Dinaikkan ke 50 supaya kandidat lebih banyak dan
# peluang menemukan berita gold yang relevan & fresh
# jadi lebih tinggi. Tidak memengaruhi logic SMC.
# =====================================================

NEWS_FETCH_LIMIT = _int_env(
    "NEWS_FETCH_LIMIT",
    50
)


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


NEWS_REQUIRE_SOURCE = _bool_env(
    "NEWS_REQUIRE_SOURCE",
    True
)


NEWS_REQUIRE_URL = _bool_env(
    "NEWS_REQUIRE_URL",
    True
)


NEWS_PREVENT_DUPLICATE = _bool_env(
    "NEWS_PREVENT_DUPLICATE",
    True
)


NEWS_TRANSLATE_TO_INDONESIAN = _bool_env(
    "NEWS_TRANSLATE_TO_INDONESIAN",
    True
)


NEWS_ENABLE_SUMMARY = _bool_env(
    "NEWS_ENABLE_SUMMARY",
    True
)


NEWS_ENABLE_GOLD_IMPACT = _bool_env(
    "NEWS_ENABLE_GOLD_IMPACT",
    True
)


NEWS_ENABLE_COMBINATION = _bool_env(
    "NEWS_ENABLE_COMBINATION",
    True
)


NEWS_CHANNEL_ID = _int_env(
    "NEWS_CHANNEL_ID",
    0
)


NEWS_REQUEST_TIMEOUT = _int_env(
    "NEWS_REQUEST_TIMEOUT",
    15
)


# =========================================================
# COMBINED AI
# =========================================================
#
# Hanya:
#
# 6 Bulan
# 12 Bulan
# Lifetime
#
# Interval:
# 90 menit
#
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


COMBINED_REQUIRE_SMC = _bool_env(
    "COMBINED_REQUIRE_SMC",
    True
)


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
# NEWS CACHE
# =========================================================

FUNDAMENTAL_NEWS_CACHE_FILE = _env(
    "FUNDAMENTAL_NEWS_CACHE_FILE",
    "data/fundamental_news.json"
)


COMBINED_NEWS_CACHE_FILE = _env(
    "COMBINED_NEWS_CACHE_FILE",
    "data/combined_news.json"
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


DEBUG_SENDER = _bool_env(
    "DEBUG_SENDER",
    False
)


# =========================================================
# SYSTEM INFO
# =========================================================

APP_NAME = _env(
    "APP_NAME",
    "XAU AI SIGNAL BOT"
)


APP_VERSION = _env(
    "APP_VERSION",
    "1.0.0"
)
