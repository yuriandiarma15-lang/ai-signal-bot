"""
CONFIG PACKAGE
XAU AI SIGNAL BOT

Menyatukan settings.py dan constants.py agar seluruh module
lama maupun module baru bisa menggunakan:

    from config import ...

atau:

    from config.settings import ...

atau:

    from config.constants import ...

File ini juga menyediakan backward compatibility untuk
nama variable konfigurasi versi lama.
"""


# =========================================================
# SETTINGS
# =========================================================

from .settings import (

    # -----------------------------------------------------
    # TELEGRAM
    # -----------------------------------------------------

    BOT_TOKEN,


    # -----------------------------------------------------
    # TWELVE DATA
    # -----------------------------------------------------

    TWELVE_TOKEN,


    # -----------------------------------------------------
    # SMC MARKET
    # -----------------------------------------------------

    SMC_SYMBOL,

    SMC_TF_STRUCTURE,
    SMC_TF_ENTRY,


    # -----------------------------------------------------
    # CANDLE
    # -----------------------------------------------------

    SMC_CANDLES_FOR_STRUCTURE,

    SMC_CANDLES_LOOKBACK,

    SMC_CANDLES_ENTRY_LOOKBACK,


    # -----------------------------------------------------
    # RISK MANAGEMENT
    # -----------------------------------------------------

    SMC_PIP_VALUE,

    SMC_SL_PIPS,

    SMC_TP1_PIPS,

    SMC_TP2_PIPS,


    SMC_SL_DISTANCE,

    SMC_TP1_DISTANCE,

    SMC_TP2_DISTANCE,


    # -----------------------------------------------------
    # ENTRY
    # -----------------------------------------------------

    SMC_MARKET_ENTRY_TOLERANCE,

    SMC_MAX_ZONE_DISTANCE,

    SMC_ZONE_TOUCH_LOOKBACK,

    SMC_MIN_ENTRY_CANDLES,


    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    SMC_PENDING_TIMEOUT_MINUTES,


    # -----------------------------------------------------
    # TELEGRAM GROUP
    # -----------------------------------------------------

    SOURCE_GROUP_ID,


    # -----------------------------------------------------
    # GOOGLE SHEET
    # -----------------------------------------------------

    SPREADSHEET_ID,

    DATA_SHEET_NAME,

    TRIAL_SHEET_NAME,


    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    ADMIN_USERNAME,


    # -----------------------------------------------------
    # RENEW
    # -----------------------------------------------------

    RENEW_BOT,


    # -----------------------------------------------------
    # TIMEZONE
    # -----------------------------------------------------

    TIMEZONE,


    # -----------------------------------------------------
    # WEBSITE
    # -----------------------------------------------------

    WEBSITE_URL,

    API_KEY,


    # -----------------------------------------------------
    # SIGNAL
    # -----------------------------------------------------

    SIGNAL_NAME,


    # -----------------------------------------------------
    # SESSION
    # -----------------------------------------------------

    SESSIONS,

    ACTIVE_HOURS_MAIN,

    ACTIVE_HOURS_EXTENDED,

    DOW_MAIN,

    DOW_EXTENDED,


    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    MAX_MESSAGE_WIDTH,


    # -----------------------------------------------------
    # LOGGING
    # -----------------------------------------------------

    LOG_LEVEL,


    # -----------------------------------------------------
    # TRIAL
    # -----------------------------------------------------

    TRIAL_MINUTES,


    # -----------------------------------------------------
    # KICK
    # -----------------------------------------------------

    KICK_DELAY_MINUTES,


    # -----------------------------------------------------
    # SIGNAL HISTORY
    # -----------------------------------------------------

    MAX_SIGNAL_HISTORY,


    # -----------------------------------------------------
    # DEBUG
    # -----------------------------------------------------

    DEBUG_SMC,
)


# =========================================================
# TWELVE DATA COMPATIBILITY
# =========================================================
#
# settings.py menggunakan:
#
#     TWELVE_TOKEN
#
# Beberapa module lama menggunakan:
#
#     TWELVEDATA_API_KEY
#
# Kita satukan supaya keduanya bekerja.
# =========================================================

TWELVEDATA_API_KEY = (
    TWELVE_TOKEN
)


# =========================================================
# CONSTANTS
# =========================================================

from .constants import (

    # -----------------------------------------------------
    # TRADING SESSION
    # -----------------------------------------------------

    START_DAY,

    END_DAY,

    START_TIME,

    END_TIME,


    # -----------------------------------------------------
    # SIGNAL
    # -----------------------------------------------------

    MAX_SIGNAL_PER_DAY,

    SIGNAL_PREFIX,


    # -----------------------------------------------------
    # SIGNAL STATUS
    # -----------------------------------------------------

    SIGNAL_ACTIVE,

    SIGNAL_PENDING,

    SIGNAL_TRIGGERED,

    SIGNAL_TP1,

    SIGNAL_TP2,

    SIGNAL_SL,

    SIGNAL_CANCELLED,

    SIGNAL_EXPIRED,


    # -----------------------------------------------------
    # ENTRY TYPE
    # -----------------------------------------------------

    ENTRY_MARKET,

    ENTRY_BUY_LIMIT,

    ENTRY_SELL_LIMIT,

    ENTRY_BUY_STOP,

    ENTRY_SELL_STOP,


    # -----------------------------------------------------
    # SMC ZONE
    # -----------------------------------------------------

    ZONE_ORDER_BLOCK,

    ZONE_FVG,

    ZONE_LIQUIDITY,


    # -----------------------------------------------------
    # SMC BIAS
    # -----------------------------------------------------

    BIAS_BULLISH,

    BIAS_BEARISH,

    BIAS_NEUTRAL,


    # -----------------------------------------------------
    # FVG FILL STATUS
    # -----------------------------------------------------

    FILL_UNTOUCHED,

    FILL_PARTIAL,

    FILL_FULL,


    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    MAX_PENDING_SIGNALS,

    PENDING_SIGNAL_CHECK_INTERVAL,


    # -----------------------------------------------------
    # TELEGRAM
    # -----------------------------------------------------

    TELEGRAM_PARSE_MODE,


    # -----------------------------------------------------
    # FORMAT
    # -----------------------------------------------------

    SIGNAL_SEPARATOR,

    # Jangan import MAX_MESSAGE_WIDTH dari constants
    # sebagai variable utama karena settings.py juga
    # memiliki konfigurasi MAX_MESSAGE_WIDTH.
)


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================
#
# Nama-nama berikut dibuat agar module lama tidak langsung
# error walaupun konfigurasi baru menggunakan prefix SMC_.
# =========================================================


# =========================================================
# MARKET
# =========================================================

SYMBOL = (
    SMC_SYMBOL
)


# =========================================================
# TIMEFRAME
# =========================================================

TF_STRUCTURE = (
    SMC_TF_STRUCTURE
)

TF_ENTRY = (
    SMC_TF_ENTRY
)


# =========================================================
# CANDLE
# =========================================================

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
# RISK
# =========================================================

SL_PIPS = (
    SMC_SL_PIPS
)

TP1_PIPS = (
    SMC_TP1_PIPS
)

TP2_PIPS = (
    SMC_TP2_PIPS
)


# =========================================================
# PRICE DISTANCE
# =========================================================

SL_DISTANCE = (
    SMC_SL_DISTANCE
)

TP1_DISTANCE = (
    SMC_TP1_DISTANCE
)

TP2_DISTANCE = (
    SMC_TP2_DISTANCE
)


# =========================================================
# ENTRY
# =========================================================

MARKET_ENTRY_TOLERANCE = (
    SMC_MARKET_ENTRY_TOLERANCE
)


# =========================================================
# ZONE
# =========================================================

MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE
)

ZONE_TOUCH_LOOKBACK = (
    SMC_ZONE_TOUCH_LOOKBACK
)

MIN_ENTRY_CANDLES = (
    SMC_MIN_ENTRY_CANDLES
)


# =========================================================
# PENDING ORDER
# =========================================================

PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# =========================================================
# SESSION
# =========================================================
#
# Tetap didefinisikan di sini juga untuk module lama yang
# mengambil variable session langsung dari config.
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


DOW_MAIN = (
    "mon,tue,wed,thu,fri"
)


DOW_EXTENDED = (
    "tue,wed,thu,fri,sat"
)


# =========================================================
# EXPORT CHECK
# =========================================================
#
# Tidak wajib digunakan, tetapi membantu memastikan package
# memiliki konfigurasi penting.
# =========================================================

__all__ = [

    # -----------------------------------------------------
    # TELEGRAM
    # -----------------------------------------------------

    "BOT_TOKEN",


    # -----------------------------------------------------
    # TWELVE DATA
    # -----------------------------------------------------

    "TWELLE_TOKEN" if False else "TWELVE_TOKEN",

    "TWELVEDATA_API_KEY",


    # -----------------------------------------------------
    # MARKET
    # -----------------------------------------------------

    "SYMBOL",

    "SMC_SYMBOL",

    "TF_STRUCTURE",

    "TF_ENTRY",


    # -----------------------------------------------------
    # CANDLE
    # -----------------------------------------------------

    "CANDLES_FOR_STRUCTURE",

    "CANDLES_LOOKBACK",

    "CANDLES_ENTRY_LOOKBACK",


    # -----------------------------------------------------
    # RISK
    # -----------------------------------------------------

    "SL_PIPS",

    "TP1_PIPS",

    "TP2_PIPS",

    "SL_DISTANCE",

    "TP1_DISTANCE",

    "TP2_DISTANCE",


    # -----------------------------------------------------
    # ENTRY
    # -----------------------------------------------------

    "MARKET_ENTRY_TOLERANCE",

    "MAX_ZONE_DISTANCE",

    "ZONE_TOUCH_LOOKBACK",

    "MIN_ENTRY_CANDLES",


    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    "PENDING_ORDER_TIMEOUT_MINUTES",


    # -----------------------------------------------------
    # TELEGRAM GROUP
    # -----------------------------------------------------

    "SOURCE_GROUP_ID",


    # -----------------------------------------------------
    # GOOGLE
    # -----------------------------------------------------

    "SPREADSHEET_ID",

    "DATA_SHEET_NAME",

    "TRIAL_SHEET_NAME",


    # -----------------------------------------------------
    # ADMIN
    # -----------------------------------------------------

    "ADMIN_USERNAME",

    "RENEW_BOT",


    # -----------------------------------------------------
    # TIMEZONE
    # -----------------------------------------------------

    "TIMEZONE",


    # -----------------------------------------------------
    # WEBSITE
    # -----------------------------------------------------

    "WEBSITE_URL",

    "API_KEY",


    # -----------------------------------------------------
    # SIGNAL
    # -----------------------------------------------------

    "SIGNAL_NAME",


    # -----------------------------------------------------
    # SESSION
    # -----------------------------------------------------

    "SESSIONS",

    "ACTIVE_HOURS_MAIN",

    "ACTIVE_HOURS_EXTENDED",

    "DOW_MAIN",

    "DOW_EXTENDED",


    # -----------------------------------------------------
    # CONSTANTS
    # -----------------------------------------------------

    "START_DAY",

    "END_DAY",

    "START_TIME",

    "END_TIME",

    "MAX_SIGNAL_PER_DAY",

    "SIGNAL_PREFIX",

    "SIGNAL_ACTIVE",

    "SIGNAL_PENDING",

    "SIGNAL_TRIGGERED",

    "SIGNAL_TP1",

    "SIGNAL_TP2",

    "SIGNAL_SL",

    "SIGNAL_CANCELLED",

    "SIGNAL_EXPIRED",

    "ENTRY_MARKET",

    "ENTRY_BUY_LIMIT",

    "ENTRY_SELL_LIMIT",

    "ENTRY_BUY_STOP",

    "ENTRY_SELL_STOP",

    "ZONE_ORDER_BLOCK",

    "ZONE_FVG",

    "ZONE_LIQUIDITY",

    "BIAS_BULLISH",

    "BIAS_BEARISH",

    "BIAS_NEUTRAL",

    "FILL_UNTOUCHED",

    "FILL_PARTIAL",

    "FILL_FULL",

    "MAX_PENDING_SIGNALS",

    "PENDING_SIGNAL_CHECK_INTERVAL",

    "TELEGRAM_PARSE_MODE",

    "SIGNAL_SEPARATOR",

    "MAX_MESSAGE_WIDTH",
]
