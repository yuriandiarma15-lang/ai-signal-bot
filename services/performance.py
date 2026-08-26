"""
services/performance.py

XAU AI SMC REAL
DAILY PERFORMANCE

Fungsi:
- Menyimpan hasil signal
- Menghitung TP1
- Menghitung TP2
- Menghitung SL
- Menghitung total pips
- Menghitung winrate
- Membuat laporan performance sederhana
- Mengirim performance ke Telegram Channel
- Menghapus data performance setelah berhasil dikirim

HASIL:
TP1 = +70 pips
TP2 = +150 pips
SL  = -50 pips

CANCEL / EXPIRED:
Tidak dihitung sebagai WIN / LOSS
dan tidak menambah / mengurangi pips.
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
# FILE
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

SL_PIPS = 50


# =========================================================
# TELEGRAM CHANNEL
# =========================================================
#
# Ambil dari environment:
#
# PERFORMANCE_CHANNEL_ID=-100xxxxxxxxxx
#
# Jangan hardcode ID channel di source code.
# =========================================================

try:

    PERFORMANCE_CHANNEL_ID = int(
        os.getenv(
            "PERFORMANCE_CHANNEL_ID",
            "0",
        )
    )

except (
    TypeError,
    ValueError,
):

    PERFORMANCE_CHANNEL_ID = 0


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
# DELETE
# =========================================================

def delete_performance_file():

    if not os.path.exists(
        PERFORMANCE_FILE
    ):

        return True

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
# SAVE SIGNAL RESULT
# =========================================================

def save_signal_result(
    item: Dict[str, Any]
):
    """
    Simpan / update hasil signal.

    Result:

        TP1
        TP2
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

            signal_time = signal_time.replace(
                tzinfo=WIB
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
    # TP2 harus dicek terlebih dahulu.
    #
    # Karena kalau TP2 terkena,
    # otomatis TP1 biasanya sudah terkena.
    #

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
            record["id"] is not None
            and
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
        "id=%s | result=%s",
        record["id"],
        result,
    )


# =========================================================
# PARSE SIGNAL DATE
# =========================================================

def _parse_signal_datetime(
    value
) -> Optional[datetime]:

    if not value:

        return None

    try:

        if isinstance(
            value,
            datetime,
        ):

            dt = value

        else:

            dt = datetime.fromisoformat(
                str(value)
            )


        if dt.tzinfo is None:

            dt = dt.replace(
                tzinfo=WIB
            )

        else:

            dt = dt.astimezone(
                WIB
            )


        return dt

    except Exception:

        return None


# =========================================================
# GET PERFORMANCE BY DATE
# =========================================================

def get_performance_by_date(
    target_date=None
):

    data = _load()


    if target_date is None:

        target_date = (
            datetime.now(
                WIB
            ).date()
        )


    result = []


    for item in data:

        dt = _parse_signal_datetime(
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

    return get_performance_by_date()


# =========================================================
# BUILD PERFORMANCE
# =========================================================

def build_performance_text(
    target_date=None
):
    """
    Membuat laporan performance sederhana.

    Format:

    07:00 BUY 4647 → TP1 +70
    08:00 SELL 4650 → TP2 +150
    09:00 BUY 4645 → SL -50

    kemudian total.
    """

    records = get_performance_by_date(
        target_date
    )


    # =====================================================
    # DATE
    # =====================================================

    if target_date is None:

        target_date = (
            datetime.now(
                WIB
            ).date()
        )


    date_text = target_date.strftime(
        "%d %B %Y"
    )


    # =====================================================
    # HEADER
    # =====================================================

    lines = [

        "📊 *XAU AI SMC REAL*",

        f"*PERFORMANCE — {date_text}*",

        "━━━━━━━━━━━━━━━━",

        "",

    ]


    # =====================================================
    # COUNTERS
    # =====================================================

    tp1_count = 0

    tp2_count = 0

    sl_count = 0

    cancel_count = 0

    total_pips = 0


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

        dt = _parse_signal_datetime(
            item.get(
                "signal_time"
            )
        )


        if dt:

            signal_time = dt.strftime(
                "%H:%M"
            )

        else:

            signal_time = "--:--"


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

        if result == "TP2":

            tp2_count += 1

            total_pips += TP2_PIPS

            result_text = (
                f"TP2 ✅ +{TP2_PIPS}"
            )


        elif result == "TP1":

            tp1_count += 1

            total_pips += TP1_PIPS

            result_text = (
                f"TP1 ✅ +{TP1_PIPS}"
            )


        elif result == "SL":

            sl_count += 1

            total_pips -= SL_PIPS

            result_text = (
                f"SL ❌ -{SL_PIPS}"
            )


        elif result == "CANCEL":

            cancel_count += 1

            result_text = (
                "EXPIRED ⚪"
            )


        else:

            continue


        # -------------------------------------------------
        # SIGNAL LINE
        # -------------------------------------------------

        lines.append(
            f"{signal_time}  {bias}  "
            f"`{entry}` → {result_text}"
        )


    # =====================================================
    # WINRATE
    # =====================================================

    wins = (
        tp1_count
        + tp2_count
    )


    losses = sl_count


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
    # SUMMARY
    # =====================================================

    lines.extend([

        "",

        "━━━━━━━━━━━━━━━━",

        "📈 *TOTAL PERFORMANCE*",

        "",

        f"TP1 : *{tp1_count}*",

        f"TP2 : *{tp2_count}*",

        f"SL  : *{sl_count}*",

        f"Expired : *{cancel_count}*",

        "",

        f"Winrate : *{winrate:.2f}%*",

        f"Total Pips : *{total_pips:+d} PIPS*",

        "",

        "━━━━━━━━━━━━━━━━",

        "",

        "🤖 *Jika Ingin trading Lebih Terstruktur*",

        "dengan bantuan AI,",

        "Aktifkan AI Assistant kalian sekarang di sini:",

        "",

        "👉 @Intradayxauusd_bot",

    ])


    return "\n".join(
        lines
    )


# =========================================================
# SEND PERFORMANCE TO CHANNEL
# =========================================================

async def send_daily_performance(
    bot,
    target_date=None,
):
    """
    Kirim performance harian ke channel Telegram.

    Dipanggil scheduler pada 04:00 WIB.

    Hanya menghapus file jika pengiriman berhasil.
    """

    # =====================================================
    # CHANNEL CHECK
    # =====================================================

    if not PERFORMANCE_CHANNEL_ID:

        logger.error(
            "PERFORMANCE_CHANNEL_ID belum "
            "dikonfigurasi."
        )

        return False


    # =====================================================
    # BUILD MESSAGE
    # =====================================================

    try:

        text = build_performance_text(
            target_date
        )

    except Exception:

        logger.exception(
            "Gagal membuat performance text."
        )

        return False


    # =====================================================
    # SEND
    # =====================================================

    try:

        await bot.send_message(

            chat_id=(
                PERFORMANCE_CHANNEL_ID
            ),

            text=text,

            parse_mode="Markdown",

            disable_web_page_preview=True,

        )


        logger.info(
            "DAILY PERFORMANCE berhasil "
            "dikirim ke channel."
        )


    except Exception:

        logger.exception(
            "Gagal mengirim daily performance."
        )

        return False


    # =====================================================
    # DELETE DATA
    # =====================================================

    delete_performance_file()


    return True


# =========================================================
# PERFORMANCE TIME
# =========================================================

def is_performance_hour(
    dt=None
):
    """
    True jika waktu menunjukkan 04:00 WIB.
    """

    if dt is None:

        now = datetime.now(
            WIB
        )

    else:

        if dt.tzinfo is None:

            now = dt.replace(
                tzinfo=WIB
            )

        else:

            now = dt.astimezone(
                WIB
            )


    return (
        now.hour == 4
        and
        now.minute == 0
    )
