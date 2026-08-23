"""
CONFIG PACKAGE

Central configuration untuk XAU AI Signal Bot.

Semua module dapat menggunakan:

    from config import ...

atau:

    from config.settings import ...
    from config.constants import ...

Backward compatibility juga disediakan untuk module lama.
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
# TWELVE DATA BACKWARD COMPATIBILITY
# =========================================================

# Nama baru
TWELVEDATA_API_KEY = TWELVE_TOKEN

# Nama lama
SYMBOL = SMC_SYMBOL


# =========================================================
# TRADING SESSION
# =========================================================

SESSIONS = [
    {
        "name": "Asian Session",
        "hours": list(range(7, 14)),
        "note": (
            "Likuiditas mulai meningkat dan harga sering "
            "membentuk range awal sebelum sesi Eropa."
        ),
    },
    {
        "name": "London Session",
        "hours": list(range(14, 20)),
        "note": (
            "Likuiditas biasanya meningkat dan peluang "
            "breakout atau displacement lebih aktif."
        ),
    },
    {
        "name": "New York Session",
        "hours": list(range(20, 24)),
        "note": (
            "Volatilitas XAUUSD cenderung tinggi terutama "
            "ketika likuiditas Amerika masuk."
        ),
    },
    {
        "name": "New York Late",
        "hours": [0, 1, 2],
        "note": (
            "Pasar memasuki fase akhir sesi New York; "
            "perhatikan exhaustion dan retracement."
        ),
    },
]


# =========================================================
# SESSION COMPATIBILITY
# =========================================================

ACTIVE_HOURS_MAIN = list(range(7, 24))

ACTIVE_HOURS_EXTENDED = [0, 1, 2]

DOW_MAIN = "mon,tue,wed,thu,fri"

DOW_EXTENDED = "tue,wed,thu,fri,sat"


# =========================================================
# ZONE DISTANCE
# =========================================================

MAX_ZONE_DISTANCE = float(
    SMC_SL_DISTANCE * 1.5
)


# =========================================================
# OPTIONAL SIGNAL SETTINGS
# =========================================================

# Minimum RR TP1
MIN_RR_TP1 = 1.20

# Minimum RR TP2
MIN_RR_TP2 = 2.00

# M1 rejection wajib untuk zona yang sudah termitigasi
REQUIRE_M1_REJECTION = True

# Partial FVG tidak langsung dijadikan market entry
ALLOW_PARTIAL_FVG_MARKET = False

# Jumlah candle M1 untuk confirmation
M1_CONFIRMATION_CANDLES = 5


# =========================================================
# LOGGING
# =========================================================

# Penting:
# Sebelumnya __init__.py mencoba mengambil LOG_LEVEL
# dari settings.py padahal variable tersebut tidak ada.
#
# Kita definisikan di sini supaya module lama tetap aman.

LOG_LEVEL = "INFO"


# =========================================================
# EXPORT LIST
# =========================================================

__all__ = [

    # Credentials / environment
    "BOT_TOKEN",
    "TWELVE_TOKEN",
    "TWELVEDATA_API_KEY",

    # Symbol
    "SMC_SYMBOL",
    "SYMBOL",

    # Timeframe
    "SMC_TF_STRUCTURE",
    "SMC_TF_ENTRY",
    "TF_STRUCTURE",
    "TF_ENTRY",

    # Candle
    "SMC_CANDLES_FOR_STRUCTURE",
    "SMC_CANDLES_LOOKBACK",
    "SMC_CANDLES_ENTRY_LOOKBACK",

    "CANDLES_FOR_STRUCTURE",
    "CANDLES_LOOKBACK",
    "CANDLES_ENTRY_LOOKBACK",

    # Pip
    "SMC_PIP_VALUE",
    "SMC_SL_PIPS",
    "SMC_TP1_PIPS",
    "SMC_TP2_PIPS",

    "SL_PIPS",
    "TP1_PIPS",
    "TP2_PIPS",

    # Distance
    "SMC_SL_DISTANCE",
    "SMC_TP1_DISTANCE",
    "SMC_TP2_DISTANCE",

    "SL_DISTANCE",
    "TP1_DISTANCE",
    "TP2_DISTANCE",

    # Entry
    "SMC_MARKET_ENTRY_TOLERANCE",
    "MARKET_ENTRY_TOLERANCE",

    # Pending
    "SMC_PENDING_TIMEOUT_MINUTES",
    "PENDING_ORDER_TIMEOUT_MINUTES",

    # Other settings
    "SOURCE_GROUP_ID",
    "SPREADSHEET_ID",
    "ADMIN_USERNAME",
    "RENEW_BOT",
    "TIMEZONE",
    "WEBSITE_URL",
    "API_KEY",

    # Constants
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

    # SMC
    "SESSIONS",
    "MAX_ZONE_DISTANCE",

    # Optional
    "MIN_RR_TP1",
    "MIN_RR_TP2",
    "REQUIRE_M1_REJECTION",
    "ALLOW_PARTIAL_FVG_MARKET",
    "M1_CONFIRMATION_CANDLES",

    # Logging
    "LOG_LEVEL",
]
