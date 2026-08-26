"""
GLOBAL SETTINGS
XAU AI SIGNAL BOT

Semua konfigurasi utama bot.

Credential diambil dari environment variable / .env

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
7. Pending order memiliki timeout 20 menit.
8. Jika dalam 20 menit tidak tersentuh:
       -> signal dianggap EXPIRED
       -> signal di-SKIP.
9. Radius pencarian zona:
       -> maksimum 100 pips.
10. Untuk XAUUSD:
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
        ValueError
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
        ValueError
    ):

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
# =========================================================
#
# File lama menggunakan:
#
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

# ---------------------------------------------------------
# STRUCTURE TIMEFRAME
# ---------------------------------------------------------
#
# Digunakan untuk membaca:
#
# - Swing High
# - Swing Low
# - BOS
# - CHoCH
# - Struktur market
# - Bias utama
#
# Default:
# M5
# ---------------------------------------------------------

SMC_TF_STRUCTURE = _env(
    "SMC_TF_STRUCTURE",
    "5min"
)


# ---------------------------------------------------------
# ENTRY TIMEFRAME
# ---------------------------------------------------------
#
# Digunakan untuk:
#
# - retest
# - rejection
# - entry precision
# - validasi M1
#
# Default:
# M1
# ---------------------------------------------------------

SMC_TF_ENTRY = _env(
    "SMC_TF_ENTRY",
    "1min"
)


TF_STRUCTURE = (
    SMC_TF_STRUCTURE
)


TF_ENTRY = (
    SMC_TF_ENTRY
)


# =========================================================
# ENTRY TIMEFRAME PRIORITY
# =========================================================
#
# Prioritas:
#
# 1. Cari zona valid M1.
# 2. Jika tidak ada -> cari zona M5.
#
# Dengan demikian:
#
# M1 valid
#       ↓
# ENTRY M1
#
# M1 tidak valid
#       ↓
# cari M5
#       ↓
# ENTRY M5
#
# Tidak ada zona
#       ↓
# NO TRADE
# =========================================================

SMC_ENTRY_PRIORITY = _env(
    "SMC_ENTRY_PRIORITY",
    "M1>M5"
)


# =========================================================
# ALLOW ENTRY TIMEFRAME
# =========================================================

SMC_ALLOW_M1_ENTRY = (
    _env(
        "SMC_ALLOW_M1_ENTRY",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


SMC_ALLOW_M5_ENTRY = (
    _env(
        "SMC_ALLOW_M5_ENTRY",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


# =========================================================
# CANDLE SETTINGS
# =========================================================

# ---------------------------------------------------------
# STRUCTURE CANDLES
# ---------------------------------------------------------
#
# Manual /signal:
#
# gunakan 12 candle M5 CLOSED.
#
# 12 x M5 = 60 menit.
# ---------------------------------------------------------

SMC_CANDLES_FOR_STRUCTURE = _int_env(
    "SMC_CANDLES_FOR_STRUCTURE",
    12
)


# ---------------------------------------------------------
# SCHEDULER LOOKBACK
# ---------------------------------------------------------
#
# Digunakan scheduler otomatis.
# ---------------------------------------------------------

SMC_CANDLES_LOOKBACK = _int_env(
    "SMC_CANDLES_LOOKBACK",
    60
)


# ---------------------------------------------------------
# ENTRY LOOKBACK
# ---------------------------------------------------------
#
# Jumlah candle untuk analisa timeframe entry.
# Default:
#
# M1 = 30 candle.
# ---------------------------------------------------------

SMC_CANDLES_ENTRY_LOOKBACK = _int_env(
    "SMC_CANDLES_ENTRY_LOOKBACK",
    30
)


# =========================================================
# BACKWARD COMPATIBILITY
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
# RISK MANAGEMENT
# =========================================================
#
# XAUUSD:
#
# 1 pip = 0.1 price
#
# Contoh:
#
# 50 pips  = 5.0 price
# 70 pips  = 7.0 price
# 150 pips = 15.0 price
# =========================================================

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


# =========================================================
# ENTRY
# =========================================================
#
# Tolerance untuk menentukan apakah harga sudah cukup
# dekat dengan zona untuk mempertimbangkan market entry.
#
# 0.3 price = 3 pips.
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
# PENTING:
#
# Sebelumnya bot menggunakan:
#
#     7.5 USD
#
# Sekarang TIDAK menggunakan USD sebagai konfigurasi.
#
# Bot menggunakan PIPS.
#
# Default:
#
#     100 pips
#
# Dengan:
#
#     1 pip = 0.1 price
#
# Maka:
#
#     100 pips = 10.0 price
#
#
# Contoh:
#
# Harga sekarang = 4622
#
# Radius 100 pips:
#
# 4612 ---------------- 4632
#
# Zona SMC yang berada di luar radius tersebut
# tidak digunakan.
# =========================================================

SMC_MAX_ZONE_DISTANCE_PIPS = _float_env(
    "SMC_MAX_ZONE_DISTANCE_PIPS",
    100
)


# ---------------------------------------------------------
# Konversi PIPS -> PRICE
# ---------------------------------------------------------

SMC_MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE_PIPS
    * SMC_PIP_VALUE
)


# ---------------------------------------------------------
# BACKWARD COMPATIBILITY
# ---------------------------------------------------------

MAX_ZONE_DISTANCE = (
    SMC_MAX_ZONE_DISTANCE
)


MAX_ZONE_DISTANCE_PIPS = (
    SMC_MAX_ZONE_DISTANCE_PIPS
)


# =========================================================
# ZONE TOUCH
# =========================================================
#
# Digunakan untuk melihat apakah zona pernah disentuh
# atau dimitigasi oleh harga sebelumnya.
# =========================================================

SMC_ZONE_TOUCH_LOOKBACK = _int_env(
    "SMC_ZONE_TOUCH_LOOKBACK",
    10
)


# =========================================================
# MIN ENTRY CANDLES
# =========================================================
#
# Minimum candle yang dibutuhkan untuk validasi entry.
# =========================================================

SMC_MIN_ENTRY_CANDLES = _int_env(
    "SMC_MIN_ENTRY_CANDLES",
    10
)


# =========================================================
# PENDING ORDER
# =========================================================
#
# Pending order hanya valid selama 20 menit.
#
# Contoh:
#
# BUY LIMIT 4615
#
# Jika dalam 20 menit:
#
# harga tidak menyentuh 4615
#
# maka:
#
# SIGNAL EXPIRED
# SKIP SIGNAL
#
# Tidak boleh entry ulang dari signal lama.
# =========================================================

SMC_PENDING_TIMEOUT_MINUTES = _int_env(
    "SMC_PENDING_TIMEOUT_MINUTES",
    20
)


PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# =========================================================
# PENDING ORDER ENABLE
# =========================================================

SMC_ENABLE_PENDING_ORDER = (
    _env(
        "SMC_ENABLE_PENDING_ORDER",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


# =========================================================
# MARKET ENTRY ENABLE
# =========================================================

SMC_ENABLE_MARKET_ENTRY = (
    _env(
        "SMC_ENABLE_MARKET_ENTRY",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
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
                2
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


# =========================================================
# SIGNAL LIMIT
# =========================================================

MAX_SIGNAL_PER_DAY = _int_env(
    "MAX_SIGNAL_PER_DAY",
    20
)


# =========================================================
# SMC VALIDATION
# =========================================================
#
# Sistem tidak boleh membuat alasan / signal berdasarkan
# kondisi yang tidak benar-benar terdeteksi.
# =========================================================

SMC_REQUIRE_VALID_ZONE = (
    _env(
        "SMC_REQUIRE_VALID_ZONE",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


# =========================================================
# REQUIRE M1 CONFIRMATION
# =========================================================
#
# Jika menggunakan MARKET ENTRY:
#
# M1 confirmation wajib.
#
# Jika belum ada confirmation:
# gunakan pending apabila zona valid.
# =========================================================

SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET = (
    _env(
        "SMC_REQUIRE_M1_CONFIRMATION_FOR_MARKET",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


# =========================================================
# FRESH ZONE PREFERENCE
# =========================================================
#
# Zona untouched / fresh lebih diprioritaskan daripada
# zona yang sudah terlalu banyak dimitigasi.
# =========================================================

SMC_PREFER_FRESH_ZONE = (
    _env(
        "SMC_PREFER_FRESH_ZONE",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
)


# =========================================================
# ALLOW MITIGATED ZONE
# =========================================================
#
# False:
# zona yang sudah terlalu termitigasi tidak digunakan.
#
# True:
# masih dapat digunakan apabila validasi lain terpenuhi.
# =========================================================

SMC_ALLOW_MITIGATED_ZONE = (
    _env(
        "SMC_ALLOW_MITIGATED_ZONE",
        "true"
    ).lower()
    in (
        "1",
        "true",
        "yes",
        "on",
    )
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

# =========================================================
# PERFORMANCE CHANNEL
# =========================================================

PERFORMANCE_CHANNEL_ID = _int_env(
    "PERFORMANCE_CHANNEL_ID",
    0
)
