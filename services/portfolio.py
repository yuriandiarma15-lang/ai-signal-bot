"""
services/portfolio.py

PORTFOLIO PERFORMANCE XAU AI SIGNAL

Fungsi:
- Mencatat setiap signal
- Mencatat Entry
- Mencatat TP1
- Mencatat TP2
- Mencatat SL
- Mencatat CANCEL
- Menghitung Win Rate
- Membuat performance message
- Menghapus data setelah performance dikirim

Performance dikirim ke Telegram Channel pada 04:00 WIB.
"""

import json
import logging
import os

from datetime import datetime
from typing import Optional, Dict, Any, List

from config.settings import TIMEZONE


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# TIMEZONE
# =========================================================

try:

    from zoneinfo import ZoneInfo

    WIB = ZoneInfo(TIMEZONE)

except Exception:

    import pytz

    WIB = pytz.timezone(TIMEZONE)


# =========================================================
# FILE
# =========================================================

DATA_DIR = "data"

PORTFOLIO_FILE = os.path.join(
    DATA_DIR,
    "portfolio.json",
)


# =========================================================
# STATUS
# =========================================================

VALID_STATUS = (
    "PENDING",
    "ENTRY",
    "TP1",
    "TP2",
    "SL",
    "CANCEL",
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

        if not isinstance(
            data,
            list,
        ):

            return []

        return data

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
# ADD SIGNAL
# =========================================================

def add_signal(
    signal,
) -> Optional[Dict[str, Any]]:

    """
    Menambahkan signal baru ke portfolio.

    Status awal:

        PENDING
    """

    data = _load()

    now = now_wib()

    # -----------------------------------------------------
    # SIGNAL DATA
    # -----------------------------------------------------

    direction = getattr(
        signal,
        "bias",
        getattr(
            signal,
            "direction",
            "",
        ),
    )

    entry_price = getattr(
        signal,
        "entry_price",
        None,
    )

    sl_price = getattr(
        signal,
        "sl",
        getattr(
            signal,
            "sl_price",
            None,
        ),
    )

    tp1_price = getattr(
        signal,
        "tp1",
        getattr(
            signal,
            "tp1_price",
            None,
        ),
    )

    tp2_price = getattr(
        signal,
        "tp2",
        getattr(
            signal,
            "tp2_price",
            None,
        ),
    )

    # -----------------------------------------------------
    # SIGNAL ID
    # -----------------------------------------------------

    signal_id = (
        now.strftime(
            "%Y%m%d_%H%M%S"
        )
        + "_"
        + str(
            len(data) + 1
        )
    )

    # -----------------------------------------------------
    # ITEM
    # -----------------------------------------------------

    item = {

        "id":
            signal_id,

        "trading_date":
            now.strftime(
                "%Y-%m-%d"
            ),

        "signal_time":
            now.isoformat(),

        "direction":
            str(
                direction
            ).upper(),

        "entry_price":
            entry_price,

        "sl_price":
            sl_price,

        "tp1_price":
            tp1_price,

        "tp2_price":
            tp2_price,

        "status":
            "PENDING",

        "entry_hit":
            False,

        "tp1_hit":
            False,

        "tp2_hit":
            False,

        "sl_hit":
            False,

        "cancelled":
            False,

        "result":
            None,

        "updated_at":
            now.isoformat(),

    }

    data.append(
        item
    )

    _save(
        data
    )

    logger.info(
        "Portfolio signal ditambahkan | "
        "%s | entry=%s",
        direction,
        entry_price,
    )

    return item


# =========================================================
# UPDATE STATUS
# =========================================================

def update_signal(
    signal_id: str,
    status: str,
):
    """
    Update hasil signal.

    Status:

        ENTRY
        TP1
        TP2
        SL
        CANCEL
    """

    status = str(
        status
    ).upper()

    if status not in VALID_STATUS:

        raise ValueError(
            f"Status tidak valid: {status}"
        )

    data = _load()

    found = None

    for item in data:

        if item.get(
            "id"
        ) == signal_id:

            found = item

            break

    if found is None:

        logger.warning(
            "Portfolio signal tidak ditemukan: %s",
            signal_id,
        )

        return None

    now = now_wib()

    found["status"] = status

    found["updated_at"] = (
        now.isoformat()
    )

    # -----------------------------------------------------
    # ENTRY
    # -----------------------------------------------------

    if status == "ENTRY":

        found["entry_hit"] = True

    # -----------------------------------------------------
    # TP1
    # -----------------------------------------------------

    elif status == "TP1":

        found["entry_hit"] = True

        found["tp1_hit"] = True

        found["result"] = "TP1"

    # -----------------------------------------------------
    # TP2
    # -----------------------------------------------------

    elif status == "TP2":

        found["entry_hit"] = True

        found["tp1_hit"] = True

        found["tp2_hit"] = True

        found["result"] = "TP2"

    # -----------------------------------------------------
    # SL
    # -----------------------------------------------------

    elif status == "SL":

        found["entry_hit"] = True

        found["sl_hit"] = True

        found["result"] = "SL"

    # -----------------------------------------------------
    # CANCEL
    # -----------------------------------------------------

    elif status == "CANCEL":

        found["cancelled"] = True

        found["result"] = "CANCEL"

    _save(
        data
    )

    logger.info(
        "Portfolio UPDATE | %s | %s",
        signal_id,
        status,
    )

    return found


# =========================================================
# UPDATE BY SIGNAL DATA
# =========================================================

def update_latest_signal(
    signal,
    status: str,
):

    """
    Update signal berdasarkan
    entry price + direction.

    Digunakan oleh monitor.py.
    """

    data = _load()

    entry_price = getattr(
        signal,
        "entry_price",
        None,
    )

    direction = getattr(
        signal,
        "bias",
        getattr(
            signal,
            "direction",
            "",
        ),
    )

    for item in reversed(
        data
    ):

        if (
            item.get(
                "entry_price"
            ) == entry_price

            and

            str(
                item.get(
                    "direction",
                    ""
                )
            ).upper()

            ==

            str(
                direction
            ).upper()
        ):

            return update_signal(
                item["id"],
                status,
            )

    return None


# =========================================================
# GET CURRENT SIGNALS
# =========================================================

def get_current_signals(
    trading_date: Optional[str] = None,
):

    data = _load()

    if trading_date is None:

        trading_date = (
            now_wib()
            .strftime(
                "%Y-%m-%d"
            )
        )

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

def calculate_statistics(
    trading_date: Optional[str] = None,
):

    signals = get_current_signals(
        trading_date
    )

    total = len(
        signals
    )

    tp1 = sum(
        1
        for s in signals
        if s.get(
            "result"
        ) == "TP1"
    )

    tp2 = sum(
        1
        for s in signals
        if s.get(
            "result"
        ) == "TP2"
    )

    sl = sum(
        1
        for s in signals
        if s.get(
            "result"
        ) == "SL"
    )

    cancel = sum(
        1
        for s in signals
        if s.get(
            "result"
        ) == "CANCEL"
    )

    # -----------------------------------------------------
    # RESOLVED
    # -----------------------------------------------------

    resolved = (
        tp1
        + tp2
        + sl
    )

    # -----------------------------------------------------
    # WIN
    # -----------------------------------------------------

    wins = (
        tp1
        + tp2
    )

    # -----------------------------------------------------
    # WIN RATE
    # -----------------------------------------------------

    if resolved > 0:

        win_rate = (
            wins
            / resolved
        ) * 100

    else:

        win_rate = 0

    return {

        "total":
            total,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "sl":
            sl,

        "cancel":
            cancel,

        "resolved":
            resolved,

        "wins":
            wins,

        "win_rate":
            round(
                win_rate,
                1,
            ),

    }


# =========================================================
# PERFORMANCE MESSAGE
# =========================================================

def build_performance_message(
    trading_date: Optional[str] = None,
) -> str:

    """
    Membuat performance Telegram.

    Format dibuat singkat dan profesional.
    """

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    if trading_date is None:

        trading_date = (
            now_wib()
            .strftime(
                "%Y-%m-%d"
            )
        )

    # -----------------------------------------------------
    # DATA
    # -----------------------------------------------------

    signals = get_current_signals(
        trading_date
    )

    stats = calculate_statistics(
        trading_date
    )

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    lines = []

    lines.append(
        "📊 XAU AI PERFORMANCE"
    )

    lines.append(
        f"📅 {trading_date}"
    )

    lines.append(
        "━━━━━━━━━━━━━━"
    )

    # -----------------------------------------------------
    # SIGNAL DETAIL
    # -----------------------------------------------------

    for index, signal in enumerate(
        signals,
        start=1,
    ):

        direction = signal.get(
            "direction",
            "-"
        )

        entry = signal.get(
            "entry_price",
            "-"
        )

        result = signal.get(
            "result"
        )

        if result is None:

            result = "PENDING"

        # -----------------------------------------------
        # TP1
        # -----------------------------------------------

        if result == "TP1":

            result_text = (
                f"TP1 "
                f"{signal.get('tp1_price', '-')}"
            )

        # -----------------------------------------------
        # TP2
        # -----------------------------------------------

        elif result == "TP2":

            result_text = (
                f"TP2 "
                f"{signal.get('tp2_price', '-')}"
            )

        # -----------------------------------------------
        # SL
        # -----------------------------------------------

        elif result == "SL":

            result_text = (
                f"SL "
                f"{signal.get('sl_price', '-')}"
            )

        # -----------------------------------------------
        # CANCEL
        # -----------------------------------------------

        elif result == "CANCEL":

            result_text = (
                "CANCEL"
            )

        # -----------------------------------------------
        # PENDING
        # -----------------------------------------------

        else:

            result_text = (
                str(
                    result
                )
            )

        lines.append(
            f"{index}. "
            f"{direction} "
            f"Entry {entry} → "
            f"{result_text}"
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    lines.append(
        "━━━━━━━━━━━━━━"
    )

    lines.append(
        f"TP1 : {stats['tp1']}"
    )

    lines.append(
        f"TP2 : {stats['tp2']}"
    )

    lines.append(
        f"SL : {stats['sl']}"
    )

    lines.append(
        f"Cancel : {stats['cancel']}"
    )

    lines.append(
        f"Win Rate : {stats['win_rate']}%"
    )

    # -----------------------------------------------------
    # TP2 RESPONSIBILITY
    # -----------------------------------------------------

    lines.append(
        "━━━━━━━━━━━━━━"
    )

    lines.append(
        "⚠️ TP2 mengikuti keputusan "
        "masing-masing trader."
    )

    lines.append(
        "Pastikan SL/BE dikelola dengan disiplin."
    )

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

    lines.append("")

    lines.append(
        "🤖 Ingin mengaktifkan AI Assistant GOLD?"
    )

    lines.append(
        "Registrasi di @Intradayxauusd_bot"
    )

    return "\n".join(
        lines
    )


# =========================================================
# GET PERFORMANCE
# =========================================================

def get_performance(
    trading_date: Optional[str] = None,
):

    """
    Mengambil performance tanpa
    menghapus data.
    """

    return build_performance_message(
        trading_date
    )


# =========================================================
# CLEAR PORTFOLIO
# =========================================================

def clear_portfolio():

    """
    Menghapus portfolio.json.

    Dipanggil SETELAH performance
    berhasil dikirim ke Telegram.
    """

    if not os.path.exists(
        PORTFOLIO_FILE
    ):

        logger.info(
            "Portfolio file tidak ada."
        )

        return True

    try:

        os.remove(
            PORTFOLIO_FILE
        )

        logger.info(
            "portfolio.json berhasil dihapus."
        )

        return True

    except Exception:

        logger.exception(
            "Gagal menghapus portfolio.json."
        )

        return False


# =========================================================
# GET PERFORMANCE AND CLEAR
# =========================================================

def get_performance_and_clear(
    trading_date: Optional[str] = None,
):

    """
    Compatibility helper.

    PERHATIAN:
    Fungsi ini hanya membuat message.

    Jangan menghapus portfolio sebelum
    Telegram berhasil mengirim.
    """

    return build_performance_message(
        trading_date
    )
