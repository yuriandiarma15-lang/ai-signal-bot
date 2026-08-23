import os
from dotenv import load_dotenv

load_dotenv()


# =========================================================
# TELEGRAM BOT
# =========================================================

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


# =========================================================
# MARKET DATA
# =========================================================

# Twelve Data API Key
TWELVE_TOKEN = os.getenv(
    "TWELVE_TOKEN"
)


# =========================================================
# SMC REAL ENGINE
# =========================================================

# Symbol utama
SMC_SYMBOL = os.getenv(
    "SMC_SYMBOL",
    "XAU/USD"
)

# Timeframe untuk membaca struktur market
SMC_TF_STRUCTURE = os.getenv(
    "SMC_TF_STRUCTURE",
    "5min"
)

# Timeframe untuk menentukan timing entry
SMC_TF_ENTRY = os.getenv(
    "SMC_TF_ENTRY",
    "1min"
)

# Jumlah candle M5 untuk analisa structure
SMC_CANDLES_FOR_STRUCTURE = int(
    os.getenv(
        "SMC_CANDLES_FOR_STRUCTURE",
        "12"
    )
)

# Lookback candle M5
SMC_CANDLES_LOOKBACK = int(
    os.getenv(
        "SMC_CANDLES_LOOKBACK",
        "60"
    )
)

# Lookback candle M1 untuk entry
SMC_CANDLES_ENTRY_LOOKBACK = int(
    os.getenv(
        "SMC_CANDLES_ENTRY_LOOKBACK",
        "30"
    )
)


# =========================================================
# RISK MANAGEMENT
# =========================================================

# Untuk XAUUSD:
# 1 pip = 0.10
#
# SL  = 50 pip  = 5.00
# TP1 = 70 pip  = 7.00
# TP2 = 150 pip = 15.00

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


# Jarak harga otomatis
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

# Toleransi agar entry dekat dengan harga market
SMC_MARKET_ENTRY_TOLERANCE = float(
    os.getenv(
        "SMC_MARKET_ENTRY_TOLERANCE",
        "0.3"
    )
)


# Pending order dianggap valid selama
# periode ini
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
    "SPREADSHEET_ID"
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME"
)


# =========================================================
# RENEW SYSTEM
# =========================================================

RENEW_BOT = os.getenv(
    "RENEW_BOT"
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
    "WEBSITE_URL"
)


API_KEY = os.getenv(
    "API_KEY"
)
