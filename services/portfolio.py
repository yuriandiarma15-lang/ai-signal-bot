"""
services/portfolio.py

XAU AI SIGNAL PORTFOLIO

Menyimpan hasil signal harian.

HASIL UTAMA:
    TP1
    SL
    CANCEL

TP2:
    Hanya dicatat untuk informasi portfolio.
    Tidak mengubah hasil utama signal.

PERFORMANCE:
    Win
    Loss
    Cancel
    Win Rate
"""

import json
import logging
import os

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import TIMEZONE


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    "portfolio"
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
# FILE
# =========================================================

DATA_DIR = "data"

PORTFOLIO_FILE = os.path.join(
    DATA_DIR,
    "portfolio.json",
)


# =========================================================
# TIME
# =========================================================

def now_wib() -> datetime:

    return datetime.now(
        WIB
    )


# =========================================================
# LOAD
# =========================================================

def _load() -> List[Dict[str, Any]]:

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

        if isinstance(
            data,
            list,
        ):

            return data

        return []

    except Exception:

        logger.exception(
            "Gagal membaca portfolio."
        )

        return []


# =========================================================
# SAVE
# =========================================================

def _save(
    data: List[Dict[str, Any]],
):

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
                indent=4,
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
# SIGNAL ID
# =========================================================

def make_signal_id(
    signal,
) -> str:

    signal_time = getattr(
        signal,
        "signal_time",
        None,
    )

    bias = str(
        getattr(
            signal,
            "bias",
            "UNKNOWN",
        )
    ).upper()

    if isinstance(
        signal_time,
        datetime,
    ):

        time_part = (
            signal_time
            .astimezone(WIB)
            .strftime(
                "%Y%m%d%H%M"
            )
        )

    else:

        time_part = now_wib().strftime(
            "%Y%m%d%H%M"
        )

    return (
        time_part
        + "_"
        + bias
    )


# =========================================================
# CREATE PORTFOLIO SIGNAL
# =========================================================

def add_signal(
    signal,
) -> Optional[str]:
    """
    Menambahkan signal baru ke portfolio.

    Hanya satu record untuk satu signal.
    """

    data = _load()

    signal_id = getattr(
        signal,
        "signal_id",
        None,
    )

    if not signal_id:

        signal_id = make_signal_id(
            signal
        )

    # -----------------------------------------------------
    # DUPLICATE
    # -----------------------------------------------------

    for item in data:

        if item.get(
            "signal_id"
        ) == signal_id:

            logger.warning(
                "Portfolio signal sudah ada: %s",
                signal_id,
            )

            return signal_id

    # -----------------------------------------------------
    # VALUES
    # -----------------------------------------------------

    entry = getattr(
        signal,
        "entry_price",
        None,
    )

    tp1 = getattr(
        signal,
        "tp1",
        None,
    )

    tp2 = getattr(
        signal,
        "tp2",
        None,
    )

    sl = getattr(
        signal,
        "sl",
        None,
    )

    bias = str(
        getattr(
            signal,
            "bias",
            "",
        )
    ).upper()

    signal_time = getattr(
        signal,
        "signal_time",
        None,
    )

    if isinstance(
        signal_time,
        datetime,
    ):

        signal_time = (
            signal_time
            .astimezone(WIB)
            .isoformat()
        )

    else:

        signal_time = now_wib().isoformat()

    # -----------------------------------------------------
    # RECORD
    # -----------------------------------------------------

    item = {

        "signal_id":
            signal_id,

        "signal_time":
            signal_time,

        "bias":
            bias,

        "entry":
            entry,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "sl":
            sl,

        # Hasil utama
        "result":
            None,

        # Waktu hasil
        "result_time":
            None,

        # TP2 hanya informasi
        "tp2_hit":
            False,

        "tp2_hit_time":
            None,

        # Status entry
        "entry_hit":
            False,

        "entry_hit_time":
            None,

    }

    data.append(
        item
    )

    _save(
        data
    )

    logger.info(
        "PORTFOLIO ADD | "
        "id=%s | bias=%s | entry=%s | tp1=%s | tp2=%s | sl=%s",
        signal_id,
        bias,
        entry,
        tp1,
        tp2,
        sl,
    )

    return signal_id


# =========================================================
# FIND SIGNAL
# =========================================================

def _find(
    signal_id: str,
):

    data = _load()

    for item in data:

        if item.get(
            "signal_id"
        ) == signal_id:

            return item

    return None


# =========================================================
# ENTRY HIT
# =========================================================

def mark_entry_hit(
    signal_id: str,
):

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal_id"
        ) != signal_id:

            continue

        if item.get(
            "entry_hit"
        ):

            return

        item["entry_hit"] = True

        item["entry_hit_time"] = (
            now_wib().isoformat()
        )

        changed = True

        break

    if changed:

        _save(
            data
        )

        logger.info(
            "PORTFOLIO ENTRY HIT | %s",
            signal_id,
        )


# =========================================================
# RESULT TP1
# =========================================================

def mark_tp1(
    signal_id: str,
):

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal_id"
        ) != signal_id:

            continue

        # -----------------------------------------------
        # TP1 adalah hasil utama
        # -----------------------------------------------

        item["result"] = "TP1"

        item["result_time"] = (
            now_wib().isoformat()
        )

        changed = True

        break

    if changed:

        _save(
            data
        )

        logger.info(
            "PORTFOLIO RESULT | %s | TP1",
            signal_id,
        )


# =========================================================
# RESULT SL
# =========================================================

def mark_sl(
    signal_id: str,
):

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal_id"
        ) != signal_id:

            continue

        # -----------------------------------------------
        # Jangan mengubah TP1 menjadi SL
        # -----------------------------------------------

        if item.get(
            "result"
        ) == "TP1":

            return

        item["result"] = "SL"

        item["result_time"] = (
            now_wib().isoformat()
        )

        changed = True

        break

    if changed:

        _save(
            data
        )

        logger.info(
            "PORTFOLIO RESULT | %s | SL",
            signal_id,
        )


# =========================================================
# RESULT CANCEL
# =========================================================

def mark_cancel(
    signal_id: str,
):

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal_id"
        ) != signal_id:

            continue

        # -----------------------------------------------
        # CANCEL hanya jika entry belum hit
        # -----------------------------------------------

        if item.get(
            "entry_hit"
        ):

            return

        item["result"] = "CANCEL"

        item["result_time"] = (
            now_wib().isoformat()
        )

        changed = True

        break

    if changed:

        _save(
            data
        )

        logger.info(
            "PORTFOLIO RESULT | %s | CANCEL",
            signal_id,
        )


# =========================================================
# TP2 HIT
# =========================================================

def mark_tp2(
    signal_id: str,
):

    data = _load()

    changed = False

    for item in data:

        if item.get(
            "signal_id"
        ) != signal_id:

            continue

        if item.get(
            "tp2_hit"
        ):

            return

        item["tp2_hit"] = True

        item["tp2_hit_time"] = (
            now_wib().isoformat()
        )

        changed = True

        break

    if changed:

        _save(
            data
        )

        logger.info(
            "PORTFOLIO TP2 HIT | %s",
            signal_id,
        )


# =========================================================
# GET TODAY
# =========================================================

def get_today() -> List[Dict[str, Any]]:
    """
    Mengambil portfolio hari ini.
    """

    data = _load()

    today = now_wib().date()

    result = []

    for item in data:

        signal_time = item.get(
            "signal_time"
        )

        try:

            dt = datetime.fromisoformat(
                signal_time
            )

            if dt.tzinfo is None:

                dt = dt.replace(
                    tzinfo=WIB
                )

            else:

                dt = dt.astimezone(
                    WIB
                )

            if dt.date() == today:

                result.append(
                    item
                )

        except Exception:

            continue

    return result


# =========================================================
# PERFORMANCE
# =========================================================

def get_performance(
    items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Menghitung performance.

    Win  = TP1
    Loss = SL
    Cancel tidak dihitung sebagai loss.
    """

    if items is None:

        items = get_today()

    total = len(
        items
    )

    win = sum(
        1
        for item in items
        if item.get("result") == "TP1"
    )

    loss = sum(
        1
        for item in items
        if item.get("result") == "SL"
    )

    cancel = sum(
        1
        for item in items
        if item.get("result") == "CANCEL"
    )

    finished = (
        win
        + loss
    )

    if finished > 0:

        win_rate = (
            win
            / finished
            * 100
        )

    else:

        win_rate = 0.0

    return {

        "total":
            total,

        "win":
            win,

        "loss":
            loss,

        "cancel":
            cancel,

        "finished":
            finished,

        "win_rate":
            round(
                win_rate,
                2,
            ),

    }


# =========================================================
# FORMAT PERFORMANCE
# =========================================================

def format_performance(
    items: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Format sederhana untuk Telegram.
    """

    if items is None:

        items = get_today()

    performance = get_performance(
        items
    )

    lines = []

    lines.append(
        "📊 *PERFORMANCE XAU AI SIGNAL*"
    )

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    # -----------------------------------------------------
    # SIGNAL LIST
    # -----------------------------------------------------

    for item in items:

        signal_time = item.get(
            "signal_time"
        )

        try:

            dt = datetime.fromisoformat(
                signal_time
            )

            hour = dt.strftime(
                "%H:%M"
            )

        except Exception:

            hour = "--:--"

        bias = item.get(
            "bias",
            "-",
        )

        entry = item.get(
            "entry",
            "-",
        )

        result = item.get(
            "result"
        )

        if result == "TP1":

            result_text = "TP1 +70 Pips"

        elif result == "SL":

            result_text = "SL -50 Pips"

        elif result == "CANCEL":

            result_text = "CANCEL"

        else:

            result_text = "OPEN"

        lines.append(
            f"🕐 {hour} | "
            f"{bias} | "
            f"Entry: {entry} | "
            f"{result_text}"
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )

    lines.append(
        f"✅ TP1 : {performance['win']}"
    )

    lines.append(
        f"❌ SL : {performance['loss']}"
    )

    lines.append(
        f"🚫 Cancel : {performance['cancel']}"
    )

    lines.append(
        f"📈 Win Rate : {performance['win_rate']}%"
    )

    lines.append(
        ""
    )

    lines.append(
        "🤖 *AI Assistant GOLD*"
    )

    lines.append(
        "Aktifkan AI Assistant GOLD:"
    )

    lines.append(
        "@Intradayxauusd_bot"
    )

    return "\n".join(
        lines
    )


# =========================================================
# CLEAR PERFORMANCE
# =========================================================

def clear_portfolio():

    try:

        if os.path.exists(
            PORTFOLIO_FILE
        ):

            os.remove(
                PORTFOLIO_FILE
            )

            logger.info(
                "Portfolio lama dihapus."
            )

    except Exception:

        logger.exception(
            "Gagal menghapus portfolio."
        )


# =========================================================
# GET ALL
# =========================================================

def get_all():

    return _load()
