"""
CONFIG PACKAGE

Menyatukan settings.py dan constants.py
agar module lama maupun module baru
bisa menggunakan:

from config import ...

atau:

from config.settings import ...
from config.constants import ...
"""

# =========================================================
# SETTINGS
# =========================================================

from .settings import (
    BOT_TOKEN,
    TWELVE_TOKEN,

    SMC_SYMBOL,

    SMC_TF_STRUCTURE,
    SMC_TF_ENTRY,

    SMC_CANDLES_FOR_STRUCTURE,
    SMC_CANDLES_LOOKBACK,
    SMC_CANDLES_ENTRY_LOOKBACK,

    SMC_PIP_VALUE,

    SMC_SL_PIPS,
    SMC_TP1_PIPS,
    SMC_TP2_PIPS,

    SMC_SL_DISTANCE,
    SMC_TP1_DISTANCE,
    SMC_TP2_DISTANCE,

    SMC_MARKET_ENTRY_TOLERANCE,
    SMC_PENDING_TIMEOUT_MINUTES,

    SOURCE_GROUP_ID,

    SPREADSHEET_ID,

    ADMIN_USERNAME,

    RENEW_BOT,

    TIMEZONE,

    WEBSITE_URL,
    API_KEY,
)


# =========================================================
# CONSTANTS
# =========================================================

from .constants import (
    START_DAY,
    END_DAY,

    START_TIME,
    END_TIME,

    MAX_SIGNAL_PER_DAY,

    SIGNAL_PREFIX,

    SIGNAL_ACTIVE,
    SIGNAL_PENDING,
    SIGNAL_TRIGGERED,
    SIGNAL_TP1,
    SIGNAL_TP2,
    SIGNAL_SL,
    SIGNAL_CANCELLED,
    SIGNAL_EXPIRED,

    ENTRY_MARKET,
    ENTRY_BUY_LIMIT,
    ENTRY_SELL_LIMIT,
    ENTRY_BUY_STOP,
    ENTRY_SELL_STOP,

    ZONE_ORDER_BLOCK,
    ZONE_FVG,
    ZONE_LIQUIDITY,

    BIAS_BULLISH,
    BIAS_BEARISH,
    BIAS_NEUTRAL,

    FILL_UNTOUCHED,
    FILL_PARTIAL,
    FILL_FULL,

    MAX_PENDING_SIGNALS,
    PENDING_SIGNAL_CHECK_INTERVAL,

    TELEGRAM_PARSE_MODE,

    SIGNAL_SEPARATOR,
    MAX_MESSAGE_WIDTH,
)


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================
#
# Ini penting karena beberapa file lama kamu masih
# menggunakan nama konfigurasi versi lama.
#
# Jadi kita tidak perlu langsung mengubah semua file.
# =========================================================

CANDLES_FOR_STRUCTURE = SMC_CANDLES_FOR_STRUCTURE

CANDLES_LOOKBACK = SMC_CANDLES_LOOKBACK

CANDLES_ENTRY_LOOKBACK = SMC_CANDLES_ENTRY_LOOKBACK

TF_STRUCTURE = SMC_TF_STRUCTURE

TF_ENTRY = SMC_TF_ENTRY

SL_DISTANCE = SMC_SL_DISTANCE

TP1_DISTANCE = SMC_TP1_DISTANCE

TP2_DISTANCE = SMC_TP2_DISTANCE

SL_PIPS = SMC_SL_PIPS

TP1_PIPS = SMC_TP1_PIPS

TP2_PIPS = SMC_TP2_PIPS

MARKET_ENTRY_TOLERANCE = SMC_MARKET_ENTRY_TOLERANCE

PENDING_ORDER_TIMEOUT_MINUTES = SMC_PENDING_TIMEOUT_MINUTES


# =========================================================
# SESSION
# =========================================================

ACTIVE_HOURS_MAIN = list(range(7, 24))

ACTIVE_HOURS_EXTENDED = [0, 1, 2]

DOW_MAIN = "mon,tue,wed,thu,fri"

DOW_EXTENDED = "tue,wed,thu,fri,sat"


# =========================================================
# MAX ZONE DISTANCE
# =========================================================

MAX_ZONE_DISTANCE = float(
    SMC_SL_DISTANCE * 1.5
)
