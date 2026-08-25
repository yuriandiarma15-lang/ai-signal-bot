"""
services/portfolio.py

XAU AI PORTFOLIO
================

Fungsi:
- Menyimpan semua signal
- Menyimpan hasil TP1 / TP2 / SL / CANCEL
- Menyimpan entry price
- Menyimpan waktu signal
- Menghitung total signal
- Menghitung TP1
- Menghitung TP2
- Menghitung SL
- Menghitung Cancel
- Menghitung Win Rate
- Mengambil performance berdasarkan tanggal

CATATAN:

TP2 TIDAK perlu disiarkan ke user saat monitoring.
TP2 hanya dicatat di portfolio.

Portfolio nantinya digunakan untuk membuat
performance report Telegram.
"""

import json
import logging
import os

from datetime import datetime
from typing import Any, Dict, List, Optional


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# TIMEZONE
# =========================================================

try:

    from zoneinfo import ZoneInfo

    WIB = ZoneInfo("Asia/Jakarta")

except Exception:

    import pytz

    WIB = pytz.timezone("Asia/Jakarta")


# =========================================================
# FILE
# =========================================================

DATA_DIR = "data"

PORTFOLIO_FILE = os.path.join(
    DATA_DIR,
    "portfolio.json",
)


# =========================================================
# VALID STATUS
# =========================================================

VALID_RESULTS = {
    "PENDING",
    "CANCEL",
    "TP1",
    "TP2",
    "SL",
}


# =========================================================
# LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:
    """
    Membaca portfolio.json.
    """

    if not os.path.exists(
        PORTFOLIO_FILE
    ):

        return []

    try:

        with open(
            PORTFOLIO_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(f)

        if not isinstance(
            data,
            list,
        ):

            logger.warning(
                "portfolio.json bukan list."
            )

            return []

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):

        logger.exception(
            "Gagal membaca portfolio."
        )

        return []


# =========================================================
# SAVE
# =========================================================

def _save(
    data: List[Dict[str, Any]]
):
    """
    Simpan portfolio secara atomic.
    """

    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    temp_file = (
        PORTFOLIO_FILE
        + ".tmp"
    )

    try:

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
            PORTFOLIO_FILE,
        )

    except Exception:

        logger.exception(
            "Gagal menyimpan portfolio."
        )

        try:

            if os.path.exists(
                temp_file
            ):

                os.remove(
                    temp_file
                )

        except OSError:

            pass

        raise


# =========================================================
# NOW
# =========================================================

def _now() -> datetime:

    return datetime.now(
        WIB
    )


# =========================================================
# DATE
# =========================================================

def _trading_date(
    dt: Optional[datetime] = None
) -> str:
    """
    Trading date mengikuti sistem bot:

    07:00 - 23:59
    + 00:00 - 06:59 dianggap
      bagian trading date sebelumnya.
    """

    if dt is None:

        dt = _now()

    if dt.tzinfo is None:

        dt = dt.replace(
            tzinfo=WIB
        )

    else:

        dt = dt.astimezone(
            WIB
        )

    if dt.hour < 7:

        from datetime import timedelta

        dt -= timedelta(
            days=1
        )

    return dt.strftime(
        "%Y-%m-%d"
    )


# =========================================================
# NORMALIZE SIGNAL
# =========================================================

def _get(
    signal,
    name: str,
    default=None,
):
    """
    Support:

    TradeSignal object
    dictionary
    """

    if isinstance(
        signal,
        dict,
    ):

        return signal.get(
            name,
            default,
        )

    return getattr(
        signal,
        name,
        default,
    )


# =========================================================
# ADD SIGNAL
# =========================================================

def add_signal(
    signal,
) -> Dict[str, Any]:
    """
    Menambahkan signal baru ke portfolio.

    Status awal:

        PENDING
    """

    data = _load()

    now = _now()

    signal_time = _get(
        signal,
        "signal_time",
    )

    if signal_time is None:

        signal_time = now.isoformat()

    elif isinstance(
        signal_time,
        datetime,
    ):

        signal_time = (
            signal_time.isoformat()
        )

    direction = _get(
        signal,
        "direction",
    )

    if direction is None:

        direction = _get(
            signal,
            "bias",
            "-",
        )

    entry_price = _get(
        signal,
        "entry_price",
    )

    sl_price = _get(
        signal,
        "sl_price",
    )

    if sl_price is None:

        sl_price = _get(
            signal,
            "sl",
        )

    tp1_price = _get(
        signal,
        "tp1_price",
    )

    if tp1_price is None:

        tp1_price = _get(
            signal,
            "tp1",
        )

    tp2_price = _get(
        signal,
        "tp2_price",
    )

    if tp2_price is None:

        tp2_price = _get(
            signal,
            "tp2",
        )

    order_type = _get(
        signal,
        "order_type",
        "-",
    )

    probability = _get(
        signal,
        "probability",
        None,
    )

    record = {

        "id":
            int(
                now.timestamp() * 1000
            ),

        "trading_date":
            _trading_date(
                now
            ),

        "signal_time":
            signal_time,

        "direction":
            str(
                direction
            ).upper(),

        "order_type":
            order_type,

        "entry_price":
            entry_price,

        "tp1_price":
            tp1_price,

        "tp2_price":
            tp2_price,

        "sl_price":
            sl_price,

        "probability":
            probability,

        # ---------------------------------------------
        # RESULT
        # ---------------------------------------------

        "result":
            "PENDING",

        # ---------------------------------------------
        # TIMING
        # ---------------------------------------------

        "entry_hit_at":
            None,

        "result_at":
            None,

        # ---------------------------------------------
        # PIPS
        # ---------------------------------------------

        "pips":
            0,

        # ---------------------------------------------
        # TP2 INTERNAL
        # ---------------------------------------------

        "tp2_hit":
            False,

        "tp2_hit_at":
            None,

        "created_at":
            now.isoformat(),

    }

    data.append(
        record
    )

    _save(
        data
    )

    logger.info(
        "Portfolio signal ditambahkan | "
        "date=%s | direction=%s | entry=%s",
        record["trading_date"],
        record["direction"],
        record["entry_price"],
    )

    return record


# =========================================================
# FIND SIGNAL
# =========================================================

def get_signal(
    signal_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Ambil signal berdasarkan ID.
    """

    data = _load()

    for item in data:

        if item.get(
            "id"
        ) == signal_id:

            return item

    return None


# =========================================================
# UPDATE RESULT
# =========================================================

def update_result(
    signal_id: int,
    result: str,
    pips: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update hasil signal.

    result:

        PENDING
        CANCEL
        TP1
        TP2
        SL

    TP2 boleh dicatat secara internal.
    """

    result = str(
        result
    ).upper()

    if result not in VALID_RESULTS:

        raise ValueError(
            "Result tidak valid: "
            + result
        )

    data = _load()

    now = _now()

    for item in data:

        if item.get(
            "id"
        ) != signal_id:

            continue

        # =============================================
        # TP2 INTERNAL
        # =============================================

        if result == "TP2":

            item["tp2_hit"] = True

            item["tp2_hit_at"] = (
                now.isoformat()
            )

            # -----------------------------------------
            # Jika sebelumnya TP1,
            # portfolio tetap boleh berubah
            # menjadi TP2.
            # -----------------------------------------

            item["result"] = "TP2"

            item["result_at"] = (
                now.isoformat()
            )

        else:

            item["result"] = result

            if pips is not None:

                item["pips"] = pips

            if result in {
                "CANCEL",
                "TP1",
                "SL",
            }:

                item["result_at"] = (
                    now.isoformat()
                )

        _save(
            data
        )

        logger.info(
            "Portfolio update | "
            "id=%s | result=%s | pips=%s",
            signal_id,
            result,
            pips,
        )

        return item

    logger.warning(
        "Portfolio signal tidak ditemukan | id=%s",
        signal_id,
    )

    return None


# =========================================================
# MARK ENTRY HIT
# =========================================================

def mark_entry_hit(
    signal_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Menandai entry sudah tersentuh.

    Tidak mengubah result menjadi TP/SL.
    """

    data = _load()

    now = _now()

    for item in data:

        if item.get(
            "id"
        ) != signal_id:

            continue

        if item.get(
            "entry_hit_at"
        ) is None:

            item["entry_hit_at"] = (
                now.isoformat()
            )

            _save(
                data
            )

        return item

    return None


# =========================================================
# MARK TP2
# =========================================================

def mark_tp2_hit(
    signal_id: int,
) -> Optional[Dict[str, Any]]:
    """
    TP2 hanya untuk portfolio.

    Tidak digunakan untuk mengirim
    notifikasi TP2 kepada user.
    """

    data = _load()

    now = _now()

    for item in data:

        if item.get(
            "id"
        ) != signal_id:

            continue

        item["tp2_hit"] = True

        item["tp2_hit_at"] = (
            now.isoformat()
        )

        # =============================================
        # Jika result masih TP1,
        # performance akhir menjadi TP2.
        # =============================================

        if item.get(
            "result"
        ) == "TP1":

            item["result"] = "TP2"

            item["result_at"] = (
                now.isoformat()
            )

        _save(
            data
        )

        logger.info(
            "TP2 HIT | portfolio only | id=%s",
            signal_id,
        )

        return item

    return None


# =========================================================
# GET ACTIVE SIGNALS
# =========================================================

def get_active_signals() -> List[Dict[str, Any]]:
    """
    Mengambil signal yang masih aktif.

    PENDING dianggap masih aktif.

    CANCEL / TP1 / TP2 / SL
    tidak dianggap aktif.
    """

    data = _load()

    return [

        item

        for item in data

        if item.get(
            "result"
        ) == "PENDING"

    ]


# =========================================================
# GET DATE
# =========================================================

def get_by_date(
    trading_date: Optional[str] = None,
) -> List[Dict[str, Any]]:

    if trading_date is None:

        trading_date = _trading_date()

    data = _load()

    return [

        item

        for item in data

        if item.get(
            "trading_date"
        ) == trading_date

    ]


# =========================================================
# STATISTICS
# =========================================================

def get_statistics(
    trading_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Menghitung performance.

    Win:

        TP1
        TP2

    Loss:

        SL

    CANCEL tidak dihitung
    sebagai win/loss.
    """

    rows = get_by_date(
        trading_date
    )

    total = len(
        rows
    )

    pending = sum(
        1
        for r in rows
        if r.get("result") == "PENDING"
    )

    cancel = sum(
        1
        for r in rows
        if r.get("result") == "CANCEL"
    )

    tp1 = sum(
        1
        for r in rows
        if r.get("result") == "TP1"
    )

    tp2 = sum(
        1
        for r in rows
        if r.get("result") == "TP2"
    )

    sl = sum(
        1
        for r in rows
        if r.get("result") == "SL"
    )

    resolved = (
        tp1
        + tp2
        + sl
    )

    wins = (
        tp1
        + tp2
    )

    if resolved > 0:

        win_rate = (
            wins
            / resolved
        ) * 100

    else:

        win_rate = 0

    total_pips = sum(
        float(
            r.get(
                "pips",
                0
            ) or 0
        )
        for r in rows
    )

    return {

        "trading_date":
            trading_date
            or _trading_date(),

        "total":
            total,

        "pending":
            pending,

        "cancel":
            cancel,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "sl":
            sl,

        "resolved":
            resolved,

        "wins":
            wins,

        "losses":
            sl,

        "win_rate":
            round(
                win_rate,
                1
            ),

        "total_pips":
            round(
                total_pips,
                1
            ),

    }


# =========================================================
# FORMAT PERFORMANCE
# =========================================================

def format_performance(
    trading_date: Optional[str] = None,
) -> str:
    """
    Format performance sederhana
    untuk channel Telegram.
    """

    rows = get_by_date(
        trading_date
    )

    stats = get_statistics(
        trading_date
    )

    if not rows:

        return (
            "📊 XAU AI PERFORMANCE\n"
            "━━━━━━━━━━━━━━\n"
            "Belum ada signal."
        )

    lines = [

        "📊 XAU AI PERFORMANCE",

        "━━━━━━━━━━━━━━",

    ]

    # =====================================================
    # SIGNAL LIST
    # =====================================================

    for row in rows:

        time_text = "-"

        signal_time = row.get(
            "signal_time"
        )

        try:

            dt = datetime.fromisoformat(
                str(
                    signal_time
                )
            )

            time_text = dt.strftime(
                "%H:%M"
            )

        except Exception:

            pass

        direction = row.get(
            "direction",
            "-",
        )

        entry = row.get(
            "entry_price",
            "-",
        )

        tp1 = row.get(
            "tp1_price",
            "-",
        )

        tp2 = row.get(
            "tp2_price",
            "-",
        )

        result = row.get(
            "result",
            "PENDING",
        )

        # ---------------------------------------------
        # FORMAT
        # ---------------------------------------------

        if result == "TP1":

            result_text = (
                "TP1"
            )

        elif result == "TP2":

            result_text = (
                "TP2"
            )

        elif result == "SL":

            result_text = (
                "SL"
            )

        elif result == "CANCEL":

            result_text = (
                "CANCEL"
            )

        else:

            result_text = (
                "PENDING"
            )

        lines.append(

            f"{time_text} "
            f"{direction} "
            f"| Entry {entry} "
            f"| TP1 {tp1} "
            f"| TP2 {tp2} "
            f"| {result_text}"

        )

    # =====================================================
    # SUMMARY
    # =====================================================

    lines.extend([

        "",

        "━━━━━━━━━━━━━━",

        f"Total : {stats['total']}",

        f"TP1   : {stats['tp1']}",

        f"TP2   : {stats['tp2']}",

        f"SL    : {stats['sl']}",

        f"Cancel: {stats['cancel']}",

        f"Win Rate : {stats['win_rate']}%",

    ])

    return "\n".join(
        lines
    )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        format_performance()
    )
