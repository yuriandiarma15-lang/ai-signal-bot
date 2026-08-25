"""
services/performance.py

XAU AI SIGNAL PERFORMANCE

Hasil utama:

TP1 = WIN
SL  = LOSS
CANCEL = tidak dihitung sebagai WIN/LOSS

TP2 hanya data tambahan portfolio.

Performance dikirim ke channel Telegram
pada jam 04:00 WIB.

Setelah berhasil dikirim,
file performance harian dihapus.
"""

import json
import logging
import os

from datetime import datetime
from typing import Any, Dict, List

from config.settings import TIMEZONE


# =========================================================
# TIMEZONE
# =========================================================

try:

    from zoneinfo import ZoneInfo

    WIB = ZoneInfo(
        TIMEZONE
    )

except Exception:

    import pytz

    WIB = pytz.timezone(
        TIMEZONE
    )


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    "performance"
)


# =========================================================
# FILE
# =========================================================

DATA_DIR = "data"

PERFORMANCE_FILE = os.path.join(
    DATA_DIR,
    "signal_performance.json",
)


# =========================================================
# LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:

    if not os.path.exists(
        PERFORMANCE_FILE
    ):

        return []

    try:

        with open(
            PERFORMANCE_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if isinstance(
            data,
            list,
        ):

            return data

    except Exception:

        logger.exception(
            "Gagal membaca performance file."
        )

    return []


# =========================================================
# SAVE
# =========================================================

def _save(
    data: List[Dict[str, Any]]
):

    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    temp = (
        PERFORMANCE_FILE
        + ".tmp"
    )

    with open(
        temp,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
        )

        f.flush()

        os.fsync(
            f.fileno()
        )

    os.replace(
        temp,
        PERFORMANCE_FILE,
    )


# =========================================================
# SAVE SIGNAL RESULT
# =========================================================

def save_signal_result(
    item: Dict[str, Any]
):

    data = _load()

    signal_time = item.get(
        "signal_time"
    )

    if isinstance(
        signal_time,
        datetime,
    ):

        signal_time_text = (
            signal_time.isoformat()
        )

    else:

        signal_time_text = str(
            signal_time
        )

    # -----------------------------------------------------
    # RESULT UTAMA
    # -----------------------------------------------------

    if item.get(
        "tp1_hit"
    ):

        result = "TP1"

    elif item.get(
        "sl_hit"
    ):

        result = "SL"

    elif item.get(
        "cancelled"
    ):

        result = "CANCEL"

    else:

        result = "OPEN"

    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

    record = {

        "id":
            item.get(
                "id"
            ),

        "signal_time":
            signal_time_text,

        "bias":
            item.get(
                "bias"
            ),

        "entry":
            item.get(
                "entry"
            ),

        "tp1":
            item.get(
                "tp1"
            ),

        "tp2":
            item.get(
                "tp2"
            ),

        "sl":
            item.get(
                "sl"
            ),

        "result":
            result,

        "tp1_hit":
            bool(
                item.get(
                    "tp1_hit",
                    False,
                )
            ),

        "tp2_hit":
            bool(
                item.get(
                    "tp2_hit",
                    False,
                )
            ),

        "sl_hit":
            bool(
                item.get(
                    "sl_hit",
                    False,
                )
            ),

        "cancelled":
            bool(
                item.get(
                    "cancelled",
                    False,
                )
            ),

        "updated_at":
            datetime.now(
                WIB
            ).isoformat(),

    }

    # -----------------------------------------------------
    # UPDATE EXISTING
    # -----------------------------------------------------

    updated = False

    for index, old in enumerate(
        data
    ):

        if old.get(
            "id"
        ) == record["id"]:

            data[index] = record

            updated = True

            break

    # -----------------------------------------------------
    # APPEND
    # -----------------------------------------------------

    if not updated:

        data.append(
            record
        )

    _save(
        data
    )

    logger.info(
        "PERFORMANCE SAVE | "
        "id=%s | result=%s | tp2=%s",
        record["id"],
        record["result"],
        record["tp2_hit"],
    )


# =========================================================
# GET TODAY
# =========================================================

def get_today_performance():

    data = _load()

    now = datetime.now(
        WIB
    )

    result = []

    for item in data:

        try:

            dt = datetime.fromisoformat(
                item["signal_time"]
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=WIB
                )

            else:

                dt = dt.astimezone(
                    WIB
                )

            if (
                dt.year == now.year
                and
                dt.month == now.month
                and
                dt.day == now.day
            ):

                result.append(
                    item
                )

        except Exception:

            continue

    result.sort(
        key=lambda x: x.get(
            "signal_time",
            ""
        )
    )

    return result


# =========================================================
# BUILD PERFORMANCE TEXT
# =========================================================

def build_performance_text():

    records = get_today_performance()

    if not records:

        return (
            "📊 *PERFORMANCE SIGNAL*\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Tidak ada signal hari ini."
        )

    lines = [

        "📊 *PERFORMANCE SIGNAL*",

        "━━━━━━━━━━━━━━━━",

        "",

    ]

    total = 0

    wins = 0

    losses = 0

    cancels = 0

    total_pips = 0

    for item in records:

        result = item.get(
            "result"
        )

        if result == "OPEN":

            continue

        signal_time = str(
            item.get(
                "signal_time",
                ""
            )
        )

        try:

            dt = datetime.fromisoformat(
                signal_time
            )

            jam = dt.strftime(
                "%H:%M"
            )

        except Exception:

            jam = "--:--"

        bias = item.get(
            "bias",
            "-"
        )

        entry = item.get(
            "entry",
            "-"
        )

        tp1 = item.get(
            "tp1",
            "-"
        )

        sl = item.get(
            "sl",
            "-"
        )

        if result == "TP1":

            result_text = (
                "✅ TP1"
            )

            wins += 1

            total_pips += 70

        elif result == "SL":

            result_text = (
                "❌ SL"
            )

            losses += 1

            total_pips -= 50

        elif result == "CANCEL":

            result_text = (
                "⚪ CANCEL"
            )

            cancels += 1

        else:

            result_text = (
                "—"
            )

        total += 1

        lines.extend([

            f"*{jam}* {bias}",

            f"Entry: `{entry}`",

            f"TP1: `{tp1}` | SL: `{sl}`",

            f"Result: {result_text}",

            "",

        ])

    # =====================================================
    # WINRATE
    # =====================================================

    counted = (
        wins
        + losses
    )

    if counted > 0:

        winrate = (
            wins
            / counted
            * 100
        )

    else:

        winrate = 0

    lines.extend([

        "━━━━━━━━━━━━━━━━",

        f"Total Signal: *{total}*",

        f"TP1: *{wins}*",

        f"SL: *{losses}*",

        f"Cancel: *{cancels}*",

        f"Winrate: *{winrate:.2f}%*",

        f"Total Pips: *{total_pips:+d}*",

        "",

        "🤖 *AI Assistant GOLD*",

        "Aktifkan AI Assistant GOLD:",

        "@Intradayxauusd_bot",

    ])

    return "\n".join(
        lines
    )


# =========================================================
# DELETE AFTER SENT
# =========================================================

def delete_performance_file():

    if not os.path.exists(
        PERFORMANCE_FILE
    ):

        return

    try:

        os.remove(
            PERFORMANCE_FILE
        )

        logger.info(
            "Performance file dihapus."
        )

    except Exception:

        logger.exception(
            "Gagal menghapus performance file."
        )
