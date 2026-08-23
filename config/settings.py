"""
GLOBAL SETTINGS
XAU AI SIGNAL BOT

Satu sumber konfigurasi utama untuk:

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
- Scheduler
- Signal

Credential diambil dari .env
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

def env(
    name: str,
    default: str = "",
) -> str:

    return os.getenv(
        name,
        default,
    ).strip()


def env_int(
    name: str,
    default: int,
) -> int:

    try:

        return int(
            env(
                name,
                str(default),
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def env_float(
    name: str,
    default: float,
) -> float:

    try:

        return float(
            env(
                name,
                str(default),
            )
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


def env_bool(
    name: str,
    default: bool = False,
) -> bool:

    value = env(
        name,
        str(default),
    ).lower()

    return value in (
        "1",
        "true",
        "yes",
        "on",
    )


# =========================================================
# TELEGRAM BOT
# =========================================================

BOT_TOKEN = env(
    "BOT_TOKEN",
)


# Kompatibilitas dengan sender lama
TELEGRAM_BOT_TOKEN = BOT_TOKEN


TELEGRAM_CHAT_ID = env(
    "TELEGRAM_CHAT_ID",
)


# =========================================================
# MARKET DATA - TWELVE DATA
# =========================================================

TWELVE_TOKEN = env(
    "TWELVE_TOKEN",
)


# Nama standar baru
TWELVEDATA_API_KEY = TWELVE_TOKEN


# =========================================================
# SYMBOL
# =========================================================

SYMBOL = env(
    "SYMBOL",
    "XAU/USD",
)


SMC_SYMBOL = env(
    "SMC_SYMBOL",
    SYMBOL,
)


# =========================================================
# TIMEZONE
# =========================================================

TIMEZONE = env(
    "SIGNAL_TIMEZONE",
    "Asia/Jakarta",
)


# =========================================================
# SMC TIMEFRAME
# =========================================================

SMC_TF_STRUCTURE = env(
    "SMC_TF_STRUCTURE",
    "5min",
)


SMC_TF_ENTRY = env(
    "SMC_TF_ENTRY",
    "1min",
)


# =========================================================
# CANDLE SETTINGS
# =========================================================

# Manual:
# 12 closed M5 candle

SMC_CANDLES_FOR_STRUCTURE = env_int(
    "SMC_CANDLES_FOR_STRUCTURE",
    12,
)


# Scheduler:
# data struktur lebih banyak

SMC_CANDLES_LOOKBACK = env_int(
    "SMC_CANDLES_LOOKBACK",
    60,
)


# M1 entry timing

SMC_CANDLES_ENTRY_LOOKBACK = env_int(
    "SMC_CANDLES_ENTRY_LOOKBACK",
    30,
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


SMC_PIP_VALUE = env_float(
    "SMC_PIP_VALUE",
    0.1,
)


SMC_SL_PIPS = env_float(
    "SMC_SL_PIPS",
    50,
)


SMC_TP1_PIPS = env_float(
    "SMC_TP1_PIPS",
    70,
)


SMC_TP2_PIPS = env_float(
    "SMC_TP2_PIPS",
    150,
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
# ENTRY SETTINGS
# =========================================================

SMC_MARKET_ENTRY_TOLERANCE = env_float(
    "SMC_MARKET_ENTRY_TOLERANCE",
    0.3,
)


SMC_MAX_ZONE_DISTANCE = env_float(
    "SMC_MAX_ZONE_DISTANCE",
    SMC_SL_DISTANCE * 1.5,
)


SMC_ZONE_TOUCH_LOOKBACK = env_int(
    "SMC_ZONE_TOUCH_LOOKBACK",
    10,
)


SMC_MIN_ENTRY_CANDLES = env_int(
    "SMC_MIN_ENTRY_CANDLES",
    10,
)


# =========================================================
# PENDING ORDER
# =========================================================

SMC_PENDING_TIMEOUT_MINUTES = env_int(
    "SMC_PENDING_TIMEOUT_MINUTES",
    20,
)


# Alias untuk file lama
PENDING_ORDER_TIMEOUT_MINUTES = (
    SMC_PENDING_TIMEOUT_MINUTES
)


# =========================================================
# SIGNAL
# =========================================================

SIGNAL_NAME = env(
    "SIGNAL_NAME",
    "XAU AI INTELLIGENCE",
)


MAX_SIGNAL_PER_DAY = env_int(
    "MAX_SIGNAL_PER_DAY",
    20,
)


MAX_SIGNAL_HISTORY = env_int(
    "MAX_SIGNAL_HISTORY",
    100,
)


# =========================================================
# GOOGLE SHEET
# =========================================================

SPREADSHEET_ID = env(
    "SPREADSHEET_ID",
)


DATA_SHEET_NAME = env(
    "DATA_SHEET_NAME",
    "data",
)


TRIAL_SHEET_NAME = env(
    "TRIAL_SHEET_NAME",
    "TRIAL",
)


# =========================================================
# ADMIN
# =========================================================

ADMIN_USERNAME = env(
    "ADMIN_USERNAME",
)


# =========================================================
# RENEW SYSTEM
# =========================================================

RENEW_BOT = env(
    "RENEW_BOT",
)


# =========================================================
# WEBSITE API
# =========================================================

WEBSITE_URL = env(
    "WEBSITE_URL",
)


API_KEY = env(
    "API_KEY",
)


# =========================================================
# SOURCE GROUP
# =========================================================

SOURCE_GROUP_ID = env_int(
    "SOURCE_GROUP_ID",
    0,
)


# =========================================================
# MARKET SESSION
# =========================================================

SESSIONS = [

    {
        "name": "Asia",

        "hours": list(
            range(7, 15)
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
            range(15, 20)
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
            list(range(20, 24))
            + [0, 1, 2]
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

# Senin-Jumat
# 07:00 - 23:00 WIB

ACTIVE_HOURS_MAIN = list(
    range(7, 24)
)


# Selasa-Sabtu
# 00:00 - 02:00 WIB

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
# TRADING SESSION
# =========================================================

START_DAY = 0

END_DAY = 5


# =========================================================
# MESSAGE
# =========================================================

MAX_MESSAGE_WIDTH = env_int(
    "MAX_MESSAGE_WIDTH",
    34,
)


TELEGRAM_PARSE_MODE = "HTML"


SIGNAL_SEPARATOR = (
    "━━━━━━━━━━━━━━"
)


# =========================================================
# TRIAL SYSTEM
# =========================================================

TRIAL_MINUTES = env_int(
    "TRIAL_MINUTES",
    30,
)


# =========================================================
# KICK / EXPIRE
# =========================================================

KICK_DELAY_MINUTES = env_int(
    "KICK_DELAY_MINUTES",
    2,
)


# =========================================================
# DEBUG
# =========================================================

DEBUG_SMC = env_bool(
    "DEBUG_SMC",
    False,
)


# =========================================================
# VALIDATION
# =========================================================

def validate_settings():
    """
    Validasi konfigurasi penting.

    Tidak membuat bot crash hanya karena
    credential belum ada, tetapi memberikan
    daftar warning yang jelas.
    """

    warnings = []

    if not BOT_TOKEN:

        warnings.append(
            "BOT_TOKEN belum diisi."
        )

    if not TWELVEDATA_API_KEY:

        warnings.append(
            "TWELVE_TOKEN belum diisi."
        )

    if not SPREADSHEET_ID:

        warnings.append(
            "SPREADSHEET_ID belum diisi."
        )

    if not WEBSITE_URL:

        warnings.append(
            "WEBSITE_URL belum diisi."
        )

    if not API_KEY:

        warnings.append(
            "API_KEY belum diisi."
        )

    return warnings


# =========================================================
# CONFIG DEBUG
# =========================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        "XAU AI SIGNAL BOT - SETTINGS"
    )

    print(
        "=========================================="
    )

    print(
        "TIMEZONE:",
        TIMEZONE,
    )

    print(
        "SYMBOL:",
        SYMBOL,
    )

    print(
        "SMC STRUCTURE:",
        SMC_TF_STRUCTURE,
    )

    print(
        "SMC ENTRY:",
        SMC_TF_ENTRY,
    )

    print(
        "SMC STRUCTURE CANDLES:",
        SMC_CANDLES_FOR_STRUCTURE,
    )

    print(
        "SMC LOOKBACK:",
        SMC_CANDLES_LOOKBACK,
    )

    print(
        "SMC ENTRY LOOKBACK:",
        SMC_CANDLES_ENTRY_LOOKBACK,
    )

    print(
        "SL:",
        SMC_SL_PIPS,
        "pip =",
        SMC_SL_DISTANCE,
    )

    print(
        "TP1:",
        SMC_TP1_PIPS,
        "pip =",
        SMC_TP1_DISTANCE,
    )

    print(
        "TP2:",
        SMC_TP2_PIPS,
        "pip =",
        SMC_TP2_DISTANCE,
    )

    print(
        "PENDING TIMEOUT:",
        SMC_PENDING_TIMEOUT_MINUTES,
        "minutes",
    )

    print(
        "TWELVE DATA KEY:",
        "SET"
        if TWELVEDATA_API_KEY
        else "NOT SET",
    )

    print(
        "BOT TOKEN:",
        "SET"
        if BOT_TOKEN
        else "NOT SET",
    )

    print(
        "=========================================="
    )

    warnings = validate_settings()

    if warnings:

        print(
            "CONFIG WARNINGS:"
        )

        for warning in warnings:

            print(
                "-",
                warning,
            )

    else:

        print(
            "CONFIG OK"
        )
