"""
Config package untuk XAU AI Signal Bot.
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

    # Signal status
    SIGNAL_ACTIVE,
    SIGNAL_PENDING,
    SIGNAL_TRIGGERED,
    SIGNAL_TP1,
    SIGNAL_TP2,
    SIGNAL_SL,
    SIGNAL_CANCELLED,
    SIGNAL_EXPIRED,

    # Entry type
    ENTRY_MARKET,
    ENTRY_BUY_LIMIT,
    ENTRY_SELL_LIMIT,
    ENTRY_BUY_STOP,
    ENTRY_SELL_STOP,

    # SMC zone
    ZONE_ORDER_BLOCK,
    ZONE_FVG,
    ZONE_LIQUIDITY,

    # SMC bias
    BIAS_BULLISH,
    BIAS_BEARISH,
    BIAS_NEUTRAL,

    # FVG
    FILL_UNTOUCHED,
    FILL_PARTIAL,
    FILL_FULL,

    # Pending
    MAX_PENDING_SIGNALS,
    PENDING_SIGNAL_CHECK_INTERVAL,

    # Telegram
    TELEGRAM_PARSE_MODE,

    # Format
    SIGNAL_SEPARATOR,
    MAX_MESSAGE_WIDTH,
)


# =========================================================
# EXPORT
# =========================================================

__all__ = [

    # =====================================================
    # SETTINGS
    # =====================================================

    "BOT_TOKEN",
    "TWELVE_TOKEN",

    "SMC_SYMBOL",

    "SMC_TF_STRUCTURE",
    "SMC_TF_ENTRY",

    "SMC_CANDLES_FOR_STRUCTURE",
    "SMC_CANDLES_LOOKBACK",
    "SMC_CANDLES_ENTRY_LOOKBACK",

    # =====================================================
    # RISK MANAGEMENT
    # =====================================================

    "SMC_PIP_VALUE",

    "SMC_SL_PIPS",
    "SMC_TP1_PIPS",
    "SMC_TP2_PIPS",

    "SMC_SL_DISTANCE",
    "SMC_TP1_DISTANCE",
    "SMC_TP2_DISTANCE",

    # =====================================================
    # ENTRY
    # =====================================================

    "SMC_MARKET_ENTRY_TOLERANCE",
    "SMC_PENDING_TIMEOUT_MINUTES",

    # =====================================================
    # TELEGRAM
    # =====================================================

    "SOURCE_GROUP_ID",

    # =====================================================
    # GOOGLE SHEET
    # =====================================================

    "SPREADSHEET_ID",

    # =====================================================
    # ADMIN
    # =====================================================

    "ADMIN_USERNAME",

    # =====================================================
    # RENEW
    # =====================================================

    "RENEW_BOT",

    # =====================================================
    # TIMEZONE
    # =====================================================

    "TIMEZONE",

    # =====================================================
    # WEBSITE
    # =====================================================

    "WEBSITE_URL",
    "API_KEY",

    # =====================================================
    # SESSION
    # =====================================================

    "START_DAY",
    "END_DAY",
    "START_TIME",
    "END_TIME",

    # =====================================================
    # SIGNAL
    # =====================================================

    "MAX_SIGNAL_PER_DAY",
    "SIGNAL_PREFIX",

    # =====================================================
    # SIGNAL STATUS
    # =====================================================

    "SIGNAL_ACTIVE",
    "SIGNAL_PENDING",
    "SIGNAL_TRIGGERED",

    "SIGNAL_TP1",
    "SIGNAL_TP2",

    "SIGNAL_SL",

    "SIGNAL_CANCELLED",
    "SIGNAL_EXPIRED",

    # =====================================================
    # ENTRY TYPE
    # =====================================================

    "ENTRY_MARKET",
    "ENTRY_BUY_LIMIT",
    "ENTRY_SELL_LIMIT",
    "ENTRY_BUY_STOP",
    "ENTRY_SELL_STOP",

    # =====================================================
    # SMC ZONE
    # =====================================================

    "ZONE_ORDER_BLOCK",
    "ZONE_FVG",
    "ZONE_LIQUIDITY",

    # =====================================================
    # SMC BIAS
    # =====================================================

    "BIAS_BULLISH",
    "BIAS_BEARISH",
    "BIAS_NEUTRAL",

    # =====================================================
    # FVG FILL
    # =====================================================

    "FILL_UNTOUCHED",
    "FILL_PARTIAL",
    "FILL_FULL",

    # =====================================================
    # PENDING
    # =====================================================

    "MAX_PENDING_SIGNALS",
    "PENDING_SIGNAL_CHECK_INTERVAL",

    # =====================================================
    # TELEGRAM FORMAT
    # =====================================================

    "TELEGRAM_PARSE_MODE",

    # =====================================================
    # FORMAT
    # =====================================================

    "SIGNAL_SEPARATOR",
    "MAX_MESSAGE_WIDTH",
]
