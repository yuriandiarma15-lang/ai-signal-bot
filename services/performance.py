"""
services/performance.py

XAU AI SIGNAL PERFORMANCE
=========================

HASIL SIGNAL:

TP1     = +70 PIPS
TP2     = +150 PIPS
SL      = -50 PIPS
EXPIRED = 0 PIPS

ATURAN:

1. Jika signal mencapai TP2:
       RESULT = TP2
       +150 PIPS

2. Jika signal hanya mencapai TP1:
       RESULT = TP1
       +70 PIPS

3. Jika signal terkena SL:
       RESULT = SL
       -50 PIPS

4. Jika entry tidak tersentuh dalam 20 menit:
       RESULT = EXPIRED
       0 PIPS

5. EXPIRED tidak dihitung sebagai WIN / LOSS.

6. TP2 TIDAK dihitung:
       TP1 +70
       kemudian TP2 +150

   Tetapi hanya:
       TP2 = +150

Dengan demikian tidak terjadi double counting.

PERFORMANCE:

Performance harian dikumpulkan sepanjang sesi.

Signal:
    07:00
    08:00
    ...
    23:00
    00:00
    01:00
    02:00

Performance dikirim ke channel:
    04:00 WIB

Setelah berhasil dikirim:
    file performance harian dapat dihapus.

"""

import json
import logging
import os

from datetime import datetime
from typing import Any, Dict, List, Optional

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
# CONFIG
# =========================================================

DATA_DIR = "data"

PERFORMANCE_FILE = os.path.join(
    DATA_DIR,
    "signal_performance.json",
)


# =========================================================
# RESULT PIPS
# =========================================================

TP1_RESULT_PIPS = int(
    SMC_TP1_PIPS
)

TP2_RESULT_PIPS = int(
    SMC_TP2_PIPS
)

SL_RESULT_PIPS = int(
    SMC_SL_PIPS
)


# =========================================================
# TIME
# =========================================================

def now_wib() -> datetime:

    return datetime.now(
        WIB
    )


# =========================================================
# SAFE INT
# =========================================================

def safe_int(
    value,
    default=0,
):

    try:

        return int(
            float(value)
        )

    except (
        TypeError,
        ValueError,
    ):

        return default


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
# PARSE DATETIME
# =========================================================

def parse_datetime(
    value: Any,
) -> Optional[datetime]:

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

        dt = dt.replace(
            tzinfo=WIB
        )

    else:

        dt = dt.astimezone(
            WIB
        )

    return dt


# =========================================================
# DETERMINE RESULT
# =========================================================

def determine_result(
    item: Dict[str, Any]
) -> str:
    """
    Menentukan hasil final signal.

    PRIORITAS:

    TP2
      ↓
    TP1
      ↓
    SL
      ↓
    EXPIRED
      ↓
    OPEN
    """

    # =====================================================
    # TP2
    # =====================================================

    if item.get(
        "tp2_hit",
        False,
    ):

        return "TP2"


    # =====================================================
    # TP1
    # =====================================================

    if item.get(
        "tp1_hit",
        False,
    ):

        return "TP1"


    # =====================================================
    # SL
    # =====================================================

    if item.get(
        "sl_hit",
        False,
    ):

        return "SL"


    # =====================================================
    # EXPIRED
    # =====================================================

    if item.get(
        "cancelled",
        False,
    ):

        return "EXPIRED"


    # =====================================================
    # TIMEOUT
    # =====================================================

    if item.get(
        "status"
    ) == "TIMEOUT":

        return "EXPIRED"


    # =====================================================
    # OPEN
    # =====================================================

    return "OPEN"


# =========================================================
# RESULT PIPS
# =========================================================

def result_pips(
    result: str,
) -> int:

    if result == "TP2":

        return TP2_RESULT_PIPS

    if result == "TP1":

        return TP1_RESULT_PIPS

    if result == "SL":

        return -SL_RESULT_PIPS

    return 0


# =========================================================
# SAVE SIGNAL RESULT
# =========================================================

def save_signal_result(
    item: Dict[str, Any]
):
    """
    Simpan / update hasil signal.

    Fungsi ini aman dipanggil berkali-kali
    untuk signal yang sama.

    Contoh:

    awal:
        OPEN

    kemudian:
        TP1

    kemudian:
        TP2

    record lama akan diperbarui.
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

    result = determine_result(
        item
    )


    # =====================================================
    # PIPS
    # =====================================================

    pips = result_pips(
        result
    )


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
        "id=%s | "
        "result=%s | "
        "pips=%s",
        record["id"],
        record["result"],
        record["pips"],
    )


# =========================================================
# GET PERFORMANCE BY DATE
# =========================================================

def get_performance_by_date(
    target_date=None,
):

    data = _load()

    if target_date is None:

        target_date = (
            now_wib().date()
        )


    result = []


    for item in data:

        dt = parse_datetime(
            item.get(
                "signal_time"
            )
        )

        if dt is None:

            continue


        if dt.date() == target_date:

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
# GET TODAY
# =========================================================

def get_today_performance():

    return get_performance_by_date(
        now_wib().date()
    )


# =========================================================
# GET PREVIOUS TRADING DAY
# =========================================================

def get_previous_performance():

    """
    Performance jam 04:00 seharusnya mengambil
    kumpulan signal dari sesi trading sebelumnya.

    Contoh:

    Rabu 04:00
        mengambil:
        Selasa 07:00
        ...
        Selasa 23:00
        Rabu 00:00
        Rabu 01:00
        Rabu 02:00

    Jadi periode performance bukan sekadar
    kalender tanggal yang sama.
    """

    now = now_wib()

    # -----------------------------------------------------
    # Jika jam 00:00 - 06:59
    #
    # performance yang baru selesai adalah
    # sesi hari sebelumnya + sesi dini hari sekarang.
    # -----------------------------------------------------

    if now.hour < 7:

        # Hari utama sebelumnya
        main_date = (
            now.date()
        )

        # Signal 07:00-23:00
        # berasal dari tanggal sebelumnya
        from datetime import timedelta

        previous_day = (
            main_date
            - timedelta(
                days=1
            )
        )

        data = _load()

        result = []


        for item in data:

            dt = parse_datetime(
                item.get(
                    "signal_time"
                )
            )

            if dt is None:

                continue


            # -------------------------------------------------
            # Previous day 07:00 - 23:59
            # -------------------------------------------------

            if (
                dt.date()
                == previous_day
                and
                dt.hour >= 7
            ):

                result.append(
                    item
                )

                continue


            # -------------------------------------------------
            # Current day 00:00 - 02:59
            # -------------------------------------------------

            if (
                dt.date()
                == main_date
                and
                dt.hour <= 2
            ):

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


    # -----------------------------------------------------
    # Jika dipanggil setelah jam 07:00,
    # fallback ke hari kalender sekarang.
    # -----------------------------------------------------

    return get_today_performance()


# =========================================================
# BUILD PERFORMANCE TEXT
# =========================================================

def build_performance_text(
    records=None,
    performance_date=None,
):
    """
    Membuat laporan performance Telegram.

    Format dibuat sederhana.

    Tidak menampilkan:
        SL price
        TP price
        detail SMC
        alasan AI

    Hanya:
        waktu
        arah
        entry
        hasil
        pips

    Kemudian summary.
    """

    if records is None:

        records = get_previous_performance()


    # =====================================================
    # HEADER DATE
    # =====================================================

    if performance_date is None:

        performance_date = (
            now_wib().date()
        )


    date_text = (
        performance_date.strftime(
            "%d-%m-%Y"
        )
    )


    # =====================================================
    # FILTER OPEN
    # =====================================================

    closed_records = [

        item

        for item in records

        if item.get(
            "result"
        ) not in (
            None,
            "OPEN",
        )

    ]


    # =====================================================
    # NO SIGNAL
    # =====================================================

    if not closed_records:

        return (
            "📊 *XAU AI SMC REAL*\n"
            f"PERFORMANCE {date_text}\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Tidak ada hasil signal.\n\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🤖 Jika Ingin trading Lebih "
            "Terstruktur dengan bantuan AI,\n"
            "Aktifkan AI Assistant kalian "
            "sekarang di sini:\n"
            "👉 @Intradayxauusd_bot"
        )


    # =====================================================
    # COUNTER
    # =====================================================

    total_signal = 0

    total_tp1 = 0

    total_tp2 = 0

    total_sl = 0

    total_expired = 0

    total_pips = 0


    # =====================================================
    # LINES
    # =====================================================

    lines = [

        "📊 *XAU AI SMC REAL*",

        f"PERFORMANCE {date_text}",

        "━━━━━━━━━━━━━━━━━━",

        "",

    ]


    # =====================================================
    # SIGNAL LIST
    # =====================================================

    for item in closed_records:

        result = item.get(
            "result"
        )


        # -------------------------------------------------
        # TIME
        # -------------------------------------------------

        dt = parse_datetime(
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

        if result == "TP1":

            emoji = "✅"

            result_text = (
                f"TP1 +{TP1_RESULT_PIPS} Pips"
            )

            total_tp1 += 1

            pips = TP1_RESULT_PIPS


        elif result == "TP2":

            emoji = "🏆"

            result_text = (
                f"TP2 +{TP2_RESULT_PIPS} Pips"
            )

            total_tp2 += 1

            pips = TP2_RESULT_PIPS


        elif result == "SL":

            emoji = "❌"

            result_text = (
                f"SL -{SL_RESULT_PIPS} Pips"
            )

            total_sl += 1

            pips = -SL_RESULT_PIPS


        elif result == "EXPIRED":

            emoji = "⚪"

            result_text = (
                "EXPIRED 0 Pips"
            )

            total_expired += 1

            pips = 0


        else:

            continue


        # -------------------------------------------------
        # TOTAL
        # -------------------------------------------------

        total_signal += 1

        total_pips += pips


        # -------------------------------------------------
        # SIGNAL LINE
        # -------------------------------------------------

        lines.append(

            f"{jam} | "
            f"{emoji} {bias} | "
            f"Entry `{entry}` | "
            f"{result_text}"

        )


    # =====================================================
    # WINRATE
    # =====================================================

    counted = (
        total_tp1
        + total_tp2
        + total_sl
    )


    if counted > 0:

        winrate = (

            (
                total_tp1
                + total_tp2
            )
            / counted
            * 100

        )

    else:

        winrate = 0.0


    # =====================================================
    # SUMMARY
    # =====================================================

    lines.extend([

        "",

        "━━━━━━━━━━━━━━━━━━",

        "📈 *HASIL HARI INI*",

        "",

        f"🎯 Total TP1 : *{total_tp1}*",

        f"🏆 Total TP2 : *{total_tp2}*",

        f"❌ Total SL  : *{total_sl}*",

        f"⚪ Expired   : *{total_expired}*",

        "",

        f"💰 TP1 Pips : *+{total_tp1 * TP1_RESULT_PIPS}*",

        f"💰 TP2 Pips : *+{total_tp2 * TP2_RESULT_PIPS}*",

        f"🔻 SL Pips  : *-{total_sl * SL_RESULT_PIPS}*",

        "",

        f"📊 *TOTAL PIPS : "
        f"{total_pips:+d}*",

        f"🔥 *WINRATE : "
        f"{winrate:.2f}%*",

        "",

        "━━━━━━━━━━━━━━━━━━",

        "",

        "🚀 *Jika Ingin trading Lebih "
        "Terstruktur dengan bantuan AI,*",

        "Aktifkan AI Assistant kalian "
        "sekarang di sini:",

        "👉 @Intradayxauusd_bot",

    ])


    return "\n".join(
        lines
    )


# =========================================================
# GET SUMMARY
# =========================================================

def get_performance_summary(
    records=None,
):

    if records is None:

        records = get_previous_performance()


    total_tp1 = 0

    total_tp2 = 0

    total_sl = 0

    total_expired = 0

    total_pips = 0


    for item in records:

        result = item.get(
            "result"
        )


        if result == "TP1":

            total_tp1 += 1

            total_pips += (
                TP1_RESULT_PIPS
            )


        elif result == "TP2":

            total_tp2 += 1

            total_pips += (
                TP2_RESULT_PIPS
            )


        elif result == "SL":

            total_sl += 1

            total_pips -= (
                SL_RESULT_PIPS
            )


        elif result == "EXPIRED":

            total_expired += 1


    counted = (
        total_tp1
        + total_tp2
        + total_sl
    )


    if counted > 0:

        winrate = (

            (
                total_tp1
                + total_tp2
            )
            / counted
            * 100

        )

    else:

        winrate = 0.0


    return {

        "tp1":
            total_tp1,

        "tp2":
            total_tp2,

        "sl":
            total_sl,

        "expired":
            total_expired,

        "total":
            (
                total_tp1
                + total_tp2
                + total_sl
                + total_expired
            ),

        "total_pips":
            total_pips,

        "winrate":
            winrate,

    }


# =========================================================
# DELETE PERFORMANCE FILE
# =========================================================

def delete_performance_file():

    if not os.path.exists(
        PERFORMANCE_FILE
    ):

        return False


    try:

        os.remove(
            PERFORMANCE_FILE
        )


        logger.info(
            "Performance file berhasil dihapus."
        )


        return True


    except Exception:

        logger.exception(
            "Gagal menghapus performance file."
        )

        return False


# =========================================================
# CLEAR ONLY SENT RECORDS
# =========================================================

def clear_records(
    record_ids: List[str],
):

    """
    Menghapus hanya record yang sudah
    berhasil dimasukkan ke performance.

    Lebih aman daripada langsung menghapus
    seluruh file.
    """

    if not record_ids:

        return


    data = _load()


    record_ids = {
        str(x)
        for x in record_ids
    }


    remaining = [

        item

        for item in data

        if str(
            item.get(
                "id"
            )
        )
        not in record_ids

    ]


    _save(
        remaining
    )


    logger.info(
        "Performance records dibersihkan | "
        "removed=%s | remaining=%s",
        len(data) - len(remaining),
        len(remaining),
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        "XAU AI SIGNAL PERFORMANCE TEST"
    )

    print(
        "=========================================="
    )

    records = get_previous_performance()


    print(
        "Records:",
        len(records)
    )


    summary = get_performance_summary(
        records
    )


    print(
        "TP1:",
        summary["tp1"]
    )

    print(
        "TP2:",
        summary["tp2"]
    )

    print(
        "SL:",
        summary["sl"]
    )

    print(
        "Expired:",
        summary["expired"]
    )

    print(
        "Total Pips:",
        summary["total_pips"]
    )

    print(
        "Winrate:",
        f'{summary["winrate"]:.2f}%'
    )


    print()
    print(
        "=========================================="
    )

    print(
        build_performance_text(
            records
        )
    )

    print(
        "=========================================="
    )
