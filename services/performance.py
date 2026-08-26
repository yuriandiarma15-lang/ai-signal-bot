"""
services/performance.py

XAU AI SMC DAILY PERFORMANCE
============================

ATURAN PERFORMANCE:

TP1  = +70 Pips
TP2  = +150 Pips
SL   = -50 Pips
CANCEL / EXPIRED = 0 Pips

KETENTUAN:

- TP1 dihitung sebagai WIN.
- Jika TP2 tercapai, hasil akhir signal = TP2.
- TP2 tidak dihitung sebagai TP1 + TP2.
- Jika SL terjadi sebelum TP1 = LOSS.
- CANCEL / EXPIRED tidak dihitung WIN / LOSS.
- Signal 07:00 sampai 23:00 dan 00:00 sampai 02:00
  dianggap sebagai satu trading session.
- Performance trading date dikirim pada 04:00 WIB.
- Data disimpan di JSON agar tidak hilang ketika bot restart.

CONTOH:

25-08-2026 23:00
26-08-2026 00:00
26-08-2026 01:00
26-08-2026 02:00

Semuanya masuk:

Trading Date = 25-08-2026

Performance dikirim:

26-08-2026 04:00 WIB
"""

import json
import logging
import os

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


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
# CONFIG
# =========================================================

DATA_DIR = "data"

PERFORMANCE_FILE = os.path.join(
    DATA_DIR,
    "signal_performance.json",
)


# =========================================================
# PERFORMANCE VALUE
# =========================================================

TP1_PIPS = 70

TP2_PIPS = 150

SL_PIPS = -50


# =========================================================
# RESULT
# =========================================================

RESULT_TP1 = "TP1"

RESULT_TP2 = "TP2"

RESULT_SL = "SL"

RESULT_CANCEL = "CANCEL"

RESULT_OPEN = "OPEN"


# =========================================================
# TIME
# =========================================================

def now_wib() -> datetime:

    return datetime.now(
        WIB
    )


# =========================================================
# PARSE DATETIME
# =========================================================

def parse_datetime(
    value: Any,
) -> Optional[datetime]:
    """
    Convert berbagai bentuk datetime
    menjadi datetime WIB.
    """

    if not value:

        return None


    if isinstance(
        value,
        datetime,
    ):

        dt = value

    else:

        try:

            dt = datetime.fromisoformat(
                str(value)
            )

        except (
            ValueError,
            TypeError,
        ):

            return None


    if dt.tzinfo is None:

        try:

            dt = dt.replace(
                tzinfo=WIB
            )

        except Exception:

            dt = WIB.localize(
                dt
            )

    else:

        dt = dt.astimezone(
            WIB
        )


    return dt


# =========================================================
# LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:
    """
    Load semua data performance.
    """

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
    """
    Atomic save.
    """

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
        PERFORMANCE_FILE
    )


# =========================================================
# TRADING DATE
# =========================================================

def get_trading_date(
    dt: Optional[datetime] = None,
) -> str:
    """
    Menentukan trading date.

    Session:

        07:00 - 23:59
        00:00 - 02:00

    Contoh:

        25 Aug 23:00
            -> 2026-08-25

        26 Aug 00:00
            -> 2026-08-25

        26 Aug 01:00
            -> 2026-08-25

        26 Aug 02:00
            -> 2026-08-25

        26 Aug 07:00
            -> 2026-08-26
    """

    if dt is None:

        dt = now_wib()

    else:

        parsed = parse_datetime(
            dt
        )

        if parsed is None:

            dt = now_wib()

        else:

            dt = parsed


    # -----------------------------------------------------
    # 00:00 - 02:59
    #
    # Masuk trading date hari sebelumnya.
    # -----------------------------------------------------

    if dt.hour < 3:

        trading_day = (
            dt.date()
            - timedelta(
                days=1
            )
        )

    else:

        trading_day = dt.date()


    return trading_day.isoformat()


# =========================================================
# GET RECORD TRADING DATE
# =========================================================

def get_performance_by_trading_date(
    trading_date: str,
) -> List[Dict[str, Any]]:
    """
    Ambil semua signal berdasarkan trading date.
    """

    data = _load()

    result = []


    for item in data:

        item_date = item.get(
            "trading_date"
        )


        if item_date == trading_date:

            result.append(
                item
            )


    result.sort(
        key=lambda x: x.get(
            "signal_time",
            ""
        )
    )


    return result


# =========================================================
# GET CURRENT TRADING PERFORMANCE
# =========================================================

def get_current_trading_performance():

    trading_date = get_trading_date()

    return get_performance_by_trading_date(
        trading_date
    )


# =========================================================
# DETERMINE RESULT
# =========================================================

def determine_result(
    item: Dict[str, Any],
) -> str:
    """
    Menentukan hasil akhir signal.

    Prioritas:

        TP2
        TP1
        SL
        CANCEL
        OPEN
    """

    # -----------------------------------------------------
    # TP2
    # -----------------------------------------------------

    if item.get(
        "tp2_hit"
    ):

        return RESULT_TP2


    # -----------------------------------------------------
    # TP1
    # -----------------------------------------------------

    if item.get(
        "tp1_hit"
    ):

        return RESULT_TP1


    # -----------------------------------------------------
    # SL
    # -----------------------------------------------------

    if item.get(
        "sl_hit"
    ):

        return RESULT_SL


    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    if item.get(
        "cancelled"
    ):

        return RESULT_CANCEL


    # -----------------------------------------------------
    # OPEN
    # -----------------------------------------------------

    return RESULT_OPEN


# =========================================================
# RESULT PIPS
# =========================================================

def result_pips(
    result: str,
) -> int:

    if result == RESULT_TP1:

        return TP1_PIPS


    if result == RESULT_TP2:

        return TP2_PIPS


    if result == RESULT_SL:

        return SL_PIPS


    return 0


# =========================================================
# SAVE SIGNAL RESULT
# =========================================================

def save_signal_result(
    item: Dict[str, Any]
):
    """
    Menyimpan / memperbarui hasil signal.

    Fungsi ini boleh dipanggil berkali-kali
    untuk signal yang sama.

    Contoh:

        OPEN
          ↓
        TP1
          ↓
        TP2

Record akan selalu diperbarui.
"""

    data = _load()


    # =====================================================
    # SIGNAL TIME
    # =====================================================

    signal_time = parse_datetime(
        item.get(
            "signal_time"
        )
    )


    if signal_time is None:

        signal_time = now_wib()


    signal_time_text = (
        signal_time.isoformat()
    )


    # =====================================================
    # SIGNAL ID
    # =====================================================

    signal_id = item.get(
        "id"
    )


    if signal_id is None:

        signal_id = (
            signal_time.strftime(
                "%Y%m%d%H%M"
            )
            + "_"
            + str(
                item.get(
                    "bias",
                    "-"
                )
            )
        )


    # =====================================================
    # RESULT
    # =====================================================

    result = determine_result(
        item
    )


    pips = result_pips(
        result
    )


    # =====================================================
    # RECORD
    # =====================================================

    record = {

        "id":
            signal_id,

        "trading_date":
            get_trading_date(
                signal_time
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

        "pips":
            pips,

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
            now_wib().isoformat(),

    }


    # =====================================================
    # UPDATE EXISTING
    # =====================================================

    updated = False


    for index, old in enumerate(
        data
    ):

        if old.get(
            "id"
        ) == signal_id:

            data[index] = record

            updated = True

            break


    # =====================================================
    # APPEND NEW
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
        "id=%s | "
        "date=%s | "
        "result=%s | "
        "pips=%s",
        signal_id,
        record["trading_date"],
        result,
        pips,
    )


# =========================================================
# CALCULATE STATISTICS
# =========================================================

def calculate_statistics(
    records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Hitung statistik performance.
    """

    total_signal = 0

    total_tp1 = 0

    total_tp2 = 0

    total_sl = 0

    total_cancel = 0

    total_open = 0

    total_pips = 0


    # =====================================================
    # LOOP
    # =====================================================

    for item in records:

        result = determine_result(
            item
        )


        # -------------------------------------------------
        # OPEN
        # -------------------------------------------------

        if result == RESULT_OPEN:

            total_open += 1

            continue


        total_signal += 1


        # -------------------------------------------------
        # TP1
        # -------------------------------------------------

        if result == RESULT_TP1:

            total_tp1 += 1

            total_pips += TP1_PIPS

            continue


        # -------------------------------------------------
        # TP2
        # -------------------------------------------------

        if result == RESULT_TP2:

            total_tp2 += 1

            total_pips += TP2_PIPS

            continue


        # -------------------------------------------------
        # SL
        # -------------------------------------------------

        if result == RESULT_SL:

            total_sl += 1

            total_pips += SL_PIPS

            continue


        # -------------------------------------------------
        # CANCEL
        # -------------------------------------------------

        if result == RESULT_CANCEL:

            total_cancel += 1

            continue


    # =====================================================
    # WINRATE
    # =====================================================

    wins = (
        total_tp1
        + total_tp2
    )


    counted = (
        wins
        + total_sl
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
    # RETURN
    # =====================================================

    return {

        "total_signal":
            total_signal,

        "total_tp1":
            total_tp1,

        "total_tp2":
            total_tp2,

        "total_sl":
            total_sl,

        "total_cancel":
            total_cancel,

        "total_open":
            total_open,

        "wins":
            wins,

        "losses":
            total_sl,

        "winrate":
            winrate,

        "total_pips":
            total_pips,

    }


# =========================================================
# FORMAT TIME
# =========================================================

def format_signal_time(
    value: Any,
) -> str:

    dt = parse_datetime(
        value
    )


    if dt is None:

        return "--:--"


    return dt.strftime(
        "%H:%M"
    )


# =========================================================
# BUILD DAILY PERFORMANCE
# =========================================================

def build_performance_text(
    trading_date: Optional[str] = None,
) -> str:
    """
    Membuat text performance harian.

    Jika trading_date tidak diberikan,
    otomatis menggunakan trading date sekarang.
    """

    if trading_date is None:

        trading_date = get_trading_date()


    records = (
        get_performance_by_trading_date(
            trading_date
        )
    )


    # =====================================================
    # HEADER
    # =====================================================

    try:

        date_obj = datetime.fromisoformat(
            trading_date
        )

        display_date = date_obj.strftime(
            "%d %B %Y"
        )

    except Exception:

        display_date = trading_date


    # =====================================================
    # NO DATA
    # =====================================================

    if not records:

        return (
            "📊 *XAU AI SMC — DAILY PERFORMANCE*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"📅 {display_date}\n\n"
            "Tidak ada signal hari ini.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🚀 Ingin trading lebih terstruktur "
            "dengan bantuan AI?\n\n"
            "Aktifkan AI Assistant kalian sekarang di sini:\n"
            "👉 @Intradayxauusd_bot"
        )


    # =====================================================
    # STATISTICS
    # =====================================================

    stats = calculate_statistics(
        records
    )


    # =====================================================
    # LINES
    # =====================================================

    lines = [

        "📊 *XAU AI SMC — DAILY PERFORMANCE*",

        "━━━━━━━━━━━━━━━━━━",

        f"📅 {display_date}",

        "",

    ]


    # =====================================================
    # SIGNAL LIST
    # =====================================================

    for item in records:

        result = determine_result(
            item
        )


        # -------------------------------------------------
        # OPEN
        # -------------------------------------------------

        if result == RESULT_OPEN:

            continue


        jam = format_signal_time(
            item.get(
                "signal_time"
            )
        )


        bias = str(
            item.get(
                "bias",
                "-"
            )
        ).upper()


        # -------------------------------------------------
        # RESULT TEXT
        # -------------------------------------------------

        if result == RESULT_TP1:

            result_text = (
                "🎯 TP1 +70 Pips"
            )


        elif result == RESULT_TP2:

            result_text = (
                "🏆 TP2 +150 Pips"
            )


        elif result == RESULT_SL:

            result_text = (
                "❌ SL -50 Pips"
            )


        elif result == RESULT_CANCEL:

            result_text = (
                "⚪ CANCEL 0 Pips"
            )


        else:

            result_text = (
                "—"
            )


        lines.append(
            f"{jam} {bias} → {result_text}"
        )


    # =====================================================
    # SUMMARY
    # =====================================================

    lines.extend([

        "",

        "━━━━━━━━━━━━━━━━━━",

        "📊 *SUMMARY*",

        "",

        f"🎯 Total TP1 : *{stats['total_tp1']}*",

        f"🏆 Total TP2 : *{stats['total_tp2']}*",

        f"❌ Total SL  : *{stats['total_sl']}*",

        "",

        f"📈 Winrate   : *{stats['winrate']:.2f}%*",

        f"💰 Total Pips: *{stats['total_pips']:+d} Pips*",

        "",

        "━━━━━━━━━━━━━━━━━━",

        "",

        "🚀 Ingin trading lebih terstruktur "
        "dengan bantuan AI?",

        "",

        "Aktifkan AI Assistant kalian sekarang di sini:",

        "👉 @Intradayxauusd_bot",

    ])


    return "\n".join(
        lines
    )


# =========================================================
# DELETE TRADING DATE
# =========================================================

def delete_trading_date(
    trading_date: str,
):
    """
    Menghapus hanya data trading date
    yang sudah berhasil dipublish.
    """

    data = _load()


    if not data:

        return


    remaining = [

        item

        for item in data

        if item.get(
            "trading_date"
        ) != trading_date

    ]


    if len(
        remaining
    ) == len(
        data
    ):

        logger.info(
            "Tidak ada data untuk dihapus | date=%s",
            trading_date,
        )

        return


    _save(
        remaining
    )


    logger.info(
        "Performance trading date dihapus | date=%s",
        trading_date,
    )


# =========================================================
# DELETE ALL
# =========================================================

def delete_performance_file():
    """
    Hapus seluruh file performance.

    Gunakan hanya jika memang diperlukan.
    """

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


# =========================================================
# GET SUMMARY
# =========================================================

def get_performance_summary(
    trading_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Mengambil summary tanpa membuat text.
    """

    if trading_date is None:

        trading_date = get_trading_date()


    records = (
        get_performance_by_trading_date(
            trading_date
        )
    )


    stats = calculate_statistics(
        records
    )


    stats[
        "trading_date"
    ] = trading_date


    return stats


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
        "NOW:",
        now_wib().strftime(
            "%d-%m-%Y %H:%M:%S WIB"
        )
    )

    print(
        "TRADING DATE:",
        get_trading_date()
    )

    print(
        "=========================================="
    )

    print(
        build_performance_text()
    )
