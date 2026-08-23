"""
GLOBAL SETTINGS
XAU AI SIGNAL BOT

Berisi seluruh konfigurasi:
- Telegram
- Twelve Data
- SMC Engine
- Risk Management
- Entry
- Google Sheet
- Admin
- Renew
- Website
- Session
- Timezone

Credential tetap diambil dari .env
"""

import os
from dotenv import load_dotenv


# =========================================================
# LOAD ENV
# =========================================================

load_dotenv()


# =========================================================
# TELEGRAM BOT
# =========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN",
    ""
)


# =========================================================
# MARKET DATA
# =========================================================

TWELVE_TOKEN = os.getenv(
    "TWELVE_TOKEN",
    ""
)


# =========================================================
# SMC REAL ENGINE
# =========================================================

SMC_SYMBOL = os.getenv(
    "SMC_SYMBOL",
    "XAU/USD"
)

SMC_TF_STRUCTURE = os.getenv(
    "SMC_TF_STRUCTURE",
    "5min"
)

SMC_TF_ENTRY = os.getenv(
    "SMC_TF_ENTRY",
    "1min"
)


# =========================================================
# CANDLE SETTINGS
# =========================================================

# Struktur utama:
# 12 candle M5 = 1 jam

SMC_CANDLES_FOR_STRUCTURE = int(
    os.getenv(
        "SMC_CANDLES_FOR_STRUCTURE",
        "12"
    )
)


# Scheduler mengambil lebih banyak candle
# supaya swing / BOS / CHoCH / OB / FVG
# memiliki data yang cukup.

SMC_CANDLES_LOOKBACK = int(
    os.getenv(
        "SMC_CANDLES_LOOKBACK",
        "60"
    )
)


# Candle M1 untuk timing entry

SMC_CANDLES_ENTRY_LOOKBACK = int(
    os.getenv(
        "SMC_CANDLES_ENTRY_LOOKBACK",
        "30"
    )
)


# =========================================================
# RISK MANAGEMENT
# =========================================================

# XAUUSD:
#
# 1 pip = 0.10
#
# SL  50 pip = 5.00
# TP1 70 pip = 7.00
# TP2 150 pip = 15.00

SMC_PIP_VALUE = float(
    os.getenv(
        "SMC_PIP_VALUE",
        "0.1"
    )
)


SMC_SL_PIPS = float(
    os.getenv(
        "SMC_SL_PIPS",
        "50"
    )
)


SMC_TP1_PIPS = float(
    os.getenv(
        "SMC_TP1_PIPS",
        "70"
    )
)


SMC_TP2_PIPS = float(
    os.getenv(
        "SMC_TP2_PIPS",
        "150"
    )
)


# =========================================================
# PRICE DISTANCE
# =========================================================

SMC_SL_DISTANCE = (
    SMC_SL_PIPS *
    SMC_PIP_VALUE
)


SMC_TP1_DISTANCE = (
    SMC_TP1_PIPS *
    SMC_PIP_VALUE
)


SMC_TP2_DISTANCE = (
    SMC_TP2_PIPS *
    SMC_PIP_VALUE
)


# =========================================================
# ENTRY SETTINGS
# =========================================================

# Jika zona sangat dekat dengan harga sekarang,
# bot boleh langsung market.

SMC_MARKET_ENTRY_TOLERANCE = float(
    os.getenv(
        "SMC_MARKET_ENTRY_TOLERANCE",
        "0.3"
    )
)


# =========================================================
# MAX ZONE DISTANCE
# =========================================================

# Zona OB/FVG yang terlalu jauh dari harga sekarang
# tidak dipaksa menjadi pending order.
#
# Default:
#
# SL = 5 USD
# MAX ZONE_DISTANCE = 7.5 USD

SMC_MAX_ZONE_DISTANCE = float(
    os.getenv(
        "SMC_MAX_ZONE_DISTANCE",
        str(SMC_SL_DISTANCE * 1.5)
    )
)


# =========================================================
# ZONE TOUCH
# =========================================================

# Jumlah candle M1 terakhir untuk validasi
# apakah zona sedang disentuh / diretest.

SMC_ZONE_TOUCH_LOOKBACK = int(
    os.getenv(
        "SMC_ZONE_TOUCH_LOOKBACK",
        "10"
    )
)


# Minimum candle entry yang harus tersedia.

SMC_MIN_ENTRY_CANDLES = int(
    os.getenv(
        "SMC_MIN_ENTRY_CANDLES",
        "10"
    )
)


# =========================================================
# PENDING ORDER
# =========================================================

SMC_PENDING_TIMEOUT_MINUTES = int(
    os.getenv(
        "SMC_PENDING_TIMEOUT_MINUTES",
        "20"
    )
)


# =========================================================
# TELEGRAM GROUP / CHANNEL
# =========================================================

SOURCE_GROUP_ID = int(
    os.getenv(
        "SOURCE_GROUP_ID",
        "0"
    )
)


# =========================================================
# GOOGLE SHEET
# =========================================================

SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID",
    ""
)


# =========================================================
# GOOGLE SHEET CONFIG
# =========================================================

# Nama sheet bisa diubah dari .env
# tanpa perlu mengubah source code.

DATA_SHEET_NAME = os.getenv(
    "DATA_SHEET_NAME",
    "data"
)

TRIAL_SHEET_NAME = os.getenv(
    "TRIAL_SHEET_NAME",
    "TRIAL"
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    ""
)


# =========================================================
# RENEW SYSTEM
# =========================================================

RENEW_BOT = os.getenv(
    "RENEW_BOT",
    ""
)


# =========================================================
# TIMEZONE
# =========================================================

TIMEZONE = os.getenv(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta"
)


# =========================================================
# WEBSITE API
# =========================================================

WEBSITE_URL = os.getenv(
    "WEBSITE_URL",
    ""
)


API_KEY = os.getenv(
    "API_KEY",
    ""
)


# =========================================================
# SIGNAL SETTINGS
# =========================================================

SIGNAL_NAME = os.getenv(
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
            "pergerakan cenderung lebih tenang "
            "dan choppy, sehingga konfirmasi "
            "struktur perlu lebih ketat"
        ),
    },


    {
        "name": "London",

        "hours": list(
            range(15, 20)
        ),

        "note": (
            "likuiditas mulai meningkat dan "
            "breakout struktur lebih sering "
            "terjadi pada XAUUSD"
        ),
    },


    {
        "name": "New York",

        "hours": (
            list(range(20, 24))
            + [0, 1, 2]
        ),

        "note": (
            "likuiditas dan volatilitas biasanya "
            "tinggi, sehingga perlu waspada "
            "spike dan berita fundamental"
        ),
    },

]


# =========================================================
# MARKET SESSION SCHEDULE
# =========================================================

# Jam utama:
# Senin - Jumat
# 07:00 - 23:00 WIB

ACTIVE_HOURS_MAIN = list(
    range(7, 24)
)


# Jam extended:
# Selasa - Sabtu
# 00:00 - 02:00 WIB

ACTIVE_HOURS_EXTENDED = [
    0,
    1,
    2,
]


# APScheduler cron

DOW_MAIN = (
    "mon,tue,wed,thu,fri"
)


DOW_EXTENDED = (
    "tue,wed,thu,fri,sat"
)


# =========================================================
# MESSAGE
# =========================================================

MAX_MESSAGE_WIDTH = int(
    os.getenv(
        "MAX_MESSAGE_WIDTH",
        "34"
    )
)


# =========================================================
# LOGGING
# =========================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)


# =========================================================
# TRIAL SYSTEM
# =========================================================

TRIAL_MINUTES = int(
    os.getenv(
        "TRIAL_MINUTES",
        "30"
    )
)


# =========================================================
# KICK / EXPIRE
# =========================================================

KICK_DELAY_MINUTES = int(
    os.getenv(
        "KICK_DELAY_MINUTES",
        "2"
    )
)


# =========================================================
# SIGNAL HISTORY
# =========================================================

MAX_SIGNAL_HISTORY = int(
    os.getenv(
        "MAX_SIGNAL_HISTORY",
        "100"
    )
)


# =========================================================
# DEBUG
# =========================================================

DEBUG_SMC = os.getenv(
    "DEBUG_SMC",
    "false"
).lower() in (
    "1",
    "true",
    "yes"
)
