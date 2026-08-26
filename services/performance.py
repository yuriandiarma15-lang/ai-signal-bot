"""
services/performance.py

XAU AI SIGNAL PERFORMANCE
=========================

Performance trading cycle:

SIGNAL:
    07:00 - 23:00 WIB
    00:00 - 02:00 WIB

REPORT:
    04:00 WIB

HASIL:

TP1 = +70 pips
TP2 = +150 pips
SL  = -50 pips
CANCEL = 0 pips dan tidak dihitung WIN/LOSS

CATATAN:
Jika TP2 tercapai:
    dihitung sebagai TP2 saja.

Bukan:
    TP1 + TP2

Contoh:

TP2:
    +150 pips

Bukan:
    +70 + 150
"""


import json
import logging
import os

from datetime import datetime, timedelta
from typing import Any, Dict, List


from config.settings import (
    TIMEZONE,
    SMC_TP1_PIPS,
    SMC_TP2_PIPS,
    SMC_SL_PIPS,
)


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
# PERFORMANCE CONFIG
# =========================================================

TP1_PIPS = int(
    SMC_TP1_PIPS
)

TP2_PIPS = int(
    SMC_TP2_PIPS
)

SL_PIPS = int(
    SMC_SL_PIPS
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

            data = json.load(
                f
            )

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

    temp_file = (
        PERFORMANCE_FILE
        + ".tmp"
    )

    with open(
        temp_file,
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
        temp_file,
        PERFORMANCE_FILE,
    )


# =========================================================
# SAVE SIGNAL RESULT
# =========================================================

def save_signal_result(
    item: Dict[str, Any]
):
    """
    Menyimpan/update hasil sebuah signal.

    Result:

        TP2
        TP1
        SL
        CANCEL
        OPEN
    """

    data = _load()


    # =====================================================
    # SIGNAL TIME
    # =====================================================

    signal_time = item.get(
        "signal_time"
    )


    if isinstance(
        signal_time,
        datetime,
    ):

        if signal_time.tzinfo is None:

            signal_time = (
                signal_time.replace(
                    tzinfo=WIB
                )
            )

        else:

            signal_time = (
                signal_time.astimezone(
                    WIB
                )
            )

        signal_time_text = (
            signal_time.isoformat()
        )

    else:

        signal_time_text = str(
            signal_time
        )


    # =====================================================
    # RESULT
    # =====================================================
    #
    # PRIORITAS:
    #
    # TP2
    # ↓
    # TP1
    # ↓
    # SL
    # ↓
    # CANCEL
    # ↓
    # OPEN
    #
    # Jika TP2 sudah hit, jangan turun menjadi TP1.
    # =====================================================

    if item.get(
        "tp2_hit"
    ):

        result = "TP2"

    elif item.get(
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


    # =====================================================
    # RECORD
    # =====================================================

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


    # =====================================================
    # UPDATE EXISTING
    # =====================================================

    updated = False


    for index, old in enumerate(
        data
    ):

        if (
            old.get("id")
            == record["id"]
        ):

            data[index] = record

            updated = True

            break


    # =====================================================
    # APPEND
    # =====================================================

    if not updated:

        data.append(
            record
        )


    # =====================================================
    # SAVE
    # =====================================================

    _save(
        data
    )


    logger.info(
        "PERFORMANCE SAVE | "
        "id=%s | result=%s | "
        "tp1=%s | tp2=%s | sl=%s",
        record["id"],
        record["result"],
        record["tp1_hit"],
        record["tp2_hit"],
        record["sl_hit"],
    )


# =========================================================
# PARSE DATETIME
# =========================================================

def _parse_datetime(
    value
):

    if not value:

        return None

    try:

        dt = datetime.fromisoformat(
            str(value)
        )

    except Exception:

        return None


    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=WIB
        )

    else:

        dt = dt.astimezone(
            WIB
        )


    return dt


# =========================================================
# GET PERFORMANCE CYCLE
# =========================================================

def get_performance_cycle():

    """
    Mengambil signal berdasarkan trading cycle.

    Contoh laporan:

    27-08-2026 04:00 WIB

    akan mengambil:

    26-08-2026 07:00
        sampai
    26-08-2026 23:59

    lalu:

    27-08-2026 00:00
        sampai
    27-08-2026 02:00
    """

    data = _load()


    now = datetime.now(
        WIB
    )


    # =====================================================
    # REPORT DATE
    # =====================================================
    #
    # Jika sekarang 04:00:
    #
    # cycle_start = kemarin 07:00
    #
    # cycle_end = hari ini 02:00
    # =====================================================

    today = now.date()

    yesterday = (
        today
        - timedelta(
            days=1
        )
    )


    cycle_start = datetime(
        yesterday.year,
        yesterday.month,
        yesterday.day,
        7,
        0,
        0,
        tzinfo=WIB,
    )


    cycle_end = datetime(
        today.year,
        today.month,
        today.day,
        2,
        0,
        0,
        tzinfo=WIB,
    )


    result = []


    for item in data:

        dt = _parse_datetime(
            item.get(
                "signal_time"
            )
        )


        if dt is None:

            continue


        # =================================================
        # CYCLE FILTER
        # =================================================

        if (
            cycle_start
            <= dt
            <= cycle_end
        ):

            result.append(
                item
            )


    # =====================================================
    # SORT
    # =====================================================

    result.sort(
        key=lambda x: (
            x.get(
                "signal_time",
                ""
            )
        )
    )


    return result


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

def get_today_performance():

    """
    Compatibility wrapper.

    Sekarang diarahkan ke trading cycle
    agar scheduler lama tetap tidak error.
    """

    return (
        get_performance_cycle()
    )


# =========================================================
# RESULT PIPS
# =========================================================

def get_result_pips(
    result
):

    if result == "TP2":

        return TP2_PIPS

    if result == "TP1":

        return TP1_PIPS

    if result == "SL":

        return -SL_PIPS

    return 0


# =========================================================
# BUILD PERFORMANCE TEXT
# =========================================================

def build_performance_text():

    records = (
        get_performance_cycle()
    )


    # =====================================================
    # HEADER
    # =====================================================

    now = datetime.now(
        WIB
    )


    report_date = (
        now
        - timedelta(
            days=1
        )
    )


    date_text = report_date.strftime(
        "%d-%m-%Y"
    )


    # =====================================================
    # EMPTY
    # =====================================================

    if not records:

        return (
            "📊 *XAU AI SMC REAL*\n"
            f"*PERFORMANCE {date_text}*\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "Tidak ada signal yang tercatat."
        )


    # =====================================================
    # COUNTERS
    # =====================================================

    total_signal = 0

    total_tp1 = 0

    total_tp2 = 0

    total_sl = 0

    total_cancel = 0

    total_pips = 0

    wins = 0

    losses = 0


    lines = [

        "📊 *XAU AI SMC REAL*",

        f"*PERFORMANCE {date_text}*",

        "━━━━━━━━━━━━━━━━",

        "",

    ]


    # =====================================================
    # SIGNAL LIST
    # =====================================================

    for item in records:

        result = item.get(
            "result"
        )


        # -------------------------------------------------
        # OPEN
        # -------------------------------------------------

        if result == "OPEN":

            continue


        # -------------------------------------------------
        # TIME
        # -------------------------------------------------

        dt = _parse_datetime(
            item.get(
                "signal_time"
            )
        )


        if dt:

            jam = dt.strftime(
                "%H:%M"
            )

        else:

            jam = "--:--"


        # -------------------------------------------------
        # BIAS
        # -------------------------------------------------

        bias = str(
            item.get(
                "bias",
                "-"
            )
        ).upper()


        # -------------------------------------------------
        # ENTRY
        # -------------------------------------------------

        entry = item.get(
            "entry",
            "-"
        )


        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        pips = get_result_pips(
            result
        )


        if result == "TP2":

            result_text = (
                f"✅ TP2 +{TP2_PIPS} pips"
            )

            total_tp2 += 1

            wins += 1


        elif result == "TP1":

            result_text = (
                f"✅ TP1 +{TP1_PIPS} pips"
            )

            total_tp1 += 1

            wins += 1


        elif result == "SL":

            result_text = (
                f"❌ SL -{SL_PIPS} pips"
            )

            total_sl += 1

            losses += 1


        elif result == "CANCEL":

            result_text = (
                "⚪ CANCEL"
            )

            total_cancel += 1


        else:

            result_text = (
                "—"
            )


        # -------------------------------------------------
        # COUNT
        # -------------------------------------------------

        total_signal += 1

        total_pips += pips


        # -------------------------------------------------
        # LINE
        # -------------------------------------------------

        lines.append(
            f"{jam} | {bias} | "
            f"`{entry}` | {result_text}"
        )


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


    # =====================================================
    # TOTAL
    # =====================================================

    lines.extend([

        "",

        "━━━━━━━━━━━━━━━━",

        f"Total Signal : *{total_signal}*",

        f"TP1          : *{total_tp1}*",

        f"TP2          : *{total_tp2}*",

        f"SL           : *{total_sl}*",

        f"Cancel       : *{total_cancel}*",

        "",

        f"Total Pips   : *{total_pips:+d} pips*",

        f"Winrate      : *{winrate:.2f}%*",

        "",

        "━━━━━━━━━━━━━━━━",

        "",

        "🤖 *AI Assistant GOLD*",

        "",

        "Jika Ingin trading Lebih Terstruktur",

        "dengan bantuan AI,",

        "Aktifkan AI Assistant kalian sekarang di sini:",

        "",

        "👉 @Intradayxauusd_bot",

    ])


    return "\n".join(
        lines
    )


# =========================================================
# DELETE PERFORMANCE FILE
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
            "Performance file dihapus setelah "
            "laporan berhasil dikirim."
        )


    except Exception:

        logger.exception(
            "Gagal menghapus performance file."
        )


# =========================================================
# DEBUG
# =========================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        "XAU AI PERFORMANCE TEST"
    )

    print(
        "=========================================="
    )

    print(
        "TP1:",
        TP1_PIPS,
        "pips"
    )

    print(
        "TP2:",
        TP2_PIPS,
        "pips"
    )

    print(
        "SL :",
        SL_PIPS,
        "pips"
    )

    print(
        "=========================================="
    )

    print(
        build_performance_text()
    )
