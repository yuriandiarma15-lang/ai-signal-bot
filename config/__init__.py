"""
CONFIG PACKAGE
XAU AI SIGNAL BOT

Semua konfigurasi dapat digunakan dengan:

    from config import BOT_TOKEN

atau:

    from config.settings import BOT_TOKEN

atau:

    from config.constants import ENTRY_MARKET
"""


# =========================================================
# IMPORT SETTINGS
# =========================================================

from .settings import *


# =========================================================
# IMPORT CONSTANTS
# =========================================================

from .constants import *


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

# ---------------------------------------------------------
# CANDLE
# ---------------------------------------------------------

CANDLES_FOR_STRUCTURE = (
    SMC_CANDLES_FOR_STRUCTURE
)

CANDLES_LOOKBACK = (
    SMC_CANDLES_LOOKBACK
)

CANDLES_ENTRY_LOOKBACK = (
    SMC_CANDLES_ENTRY_LOOKBACK
)


# ---------------------------------------------------------
# TIMEFRAME
# ---------------------------------------------------------

TF_STRUCTURE = (
    SMC_TF_STRUCTURE
)

TF_ENTRY = (
    SMC_TF_ENTRY
)


# ---------------------------------------------------------
# RISK
# ---------------------------------------------------------

SL_DISTANCE = (
    SMC_SL_DISTANCE
)

TP1_DISTANCE = (
    SMC_TP1_DISTANCE
)

TP2_DISTANCE = (
    SMC_TP2_DISTANCE
)

SL_PIPS = (
    SMC_SL_PIPS
)

TP1_PIPS = (
    SMC_TP1_PIPS
)

TP2_PIPS = (
    SMC_TP2_PIPS
)


# ---------------------------------------------------------
# ENTRY
# ---------------------------------------------------------

MARKET_ENTRY_TOLERANCE = (
    SMC_MARKET_ENTRY_TOLERANCE
)


# ---------------------------------------------------------
# ZONE
# ---------------------------------------------------------

MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE
)


# ---------------------------------------------------------
# PENDING
# ---------------------------------------------------------

PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# ---------------------------------------------------------
# TWELVE DATA
#
# File lama:
# TWELVEDATA_API_KEY
#
# File baru:
# TWELVE_TOKEN
# ---------------------------------------------------------

TWELVEDATA_API_KEY = (
    TWELVE_TOKEN
)


# ---------------------------------------------------------
# SYMBOL
# ---------------------------------------------------------

SYMBOL = (
    SMC_SYMBOL
)
