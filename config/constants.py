from datetime import time


# =========================================================
# TRADING SESSION
# =========================================================

START_DAY = 0
# Monday

END_DAY = 5
# Saturday


START_TIME = time(
    7,
    0
)

END_TIME = time(
    2,
    0
)


# =========================================================
# SIGNAL
# =========================================================

MAX_SIGNAL_PER_DAY = 20


SIGNAL_PREFIX = """
━━━━━━━━━━━━━━

🤖 <b>XAU AI ASSISTANT</b>

"""


# =========================================================
# SIGNAL STATUS
# =========================================================

SIGNAL_ACTIVE = "ACTIVE"

SIGNAL_PENDING = "PENDING"

SIGNAL_TRIGGERED = "TRIGGERED"

SIGNAL_TP1 = "TP1 HIT"

SIGNAL_TP2 = "TP2 HIT"

SIGNAL_SL = "SL HIT"

SIGNAL_CANCELLED = "CANCELLED"

SIGNAL_EXPIRED = "EXPIRED"


# =========================================================
# ENTRY TYPE
# =========================================================

ENTRY_MARKET = "Market"

ENTRY_BUY_LIMIT = "Buy Limit"

ENTRY_SELL_LIMIT = "Sell Limit"

ENTRY_BUY_STOP = "Buy Stop"

ENTRY_SELL_STOP = "Sell Stop"


# =========================================================
# SMC ZONE TYPE
# =========================================================

ZONE_ORDER_BLOCK = "Order Block"

ZONE_FVG = "Fair Value Gap"

ZONE_LIQUIDITY = "Liquidity"


# =========================================================
# SMC BIAS
# =========================================================

BIAS_BULLISH = "bullish"

BIAS_BEARISH = "bearish"

BIAS_NEUTRAL = "neutral"


# =========================================================
# FVG FILL STATUS
# =========================================================

FILL_UNTOUCHED = "untouched"

FILL_PARTIAL = "partial"

FILL_FULL = "full"


# =========================================================
# SIGNAL LIMIT
# =========================================================

MAX_PENDING_SIGNALS = 10

PENDING_SIGNAL_CHECK_INTERVAL = 60


# =========================================================
# TELEGRAM
# =========================================================

TELEGRAM_PARSE_MODE = "HTML"


# =========================================================
# FORMAT
# =========================================================

SIGNAL_SEPARATOR = "━━━━━━━━━━━━━━"

MAX_MESSAGE_WIDTH = 34
