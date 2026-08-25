"""
services/monitor.py

XAU AI SIGNAL MONITOR

RULE:

1. Scan harga setiap 5 menit.
2. Entry maksimal ditunggu 20 menit.
3. Entry tidak kena -> CANCEL.
4. Entry kena -> monitor TP1 + SL.
5. TP1 kena -> hasil utama PROFIT +70 pips.
6. Setelah TP1 kena:
   - SL tidak lagi dihitung sebagai LOSS.
   - TP2 hanya dicatat untuk portfolio.
7. TP2 tidak dikirim ke Telegram.
8. Jika sampai menit :59 TP1/SL belum kena:
   - monitoring dihentikan.
   - kirim pesan penutupan.
9. Data hasil disimpan untuk performance.
"""

import asyncio
import logging

from datetime import datetime
from typing import Any, Dict, List, Optional

from config.settings import TIMEZONE

from services.market import get_price
from services.sender import send_signal_to_members

from services.performance import (
    save_signal_result,
)


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
# LOGGER
# =========================================================

logger = logging.getLogger(
    "signal_monitor"
)


# =========================================================
# CONFIG
# =========================================================

# Scan setiap 5 menit
MONITOR_INTERVAL_MINUTES = 5

# Entry maksimal ditunggu 20 menit
ENTRY_TIMEOUT_MINUTES = 20

# Monitoring TP1 / SL berhenti pada menit 59
MONITOR_END_MINUTE = 59


# =========================================================
# ACTIVE SIGNALS
# =========================================================

_active_signals: List[
    Dict[str, Any]
] = []


# =========================================================
# LOCK
# =========================================================

_monitor_lock = asyncio.Lock()


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
# PRICE FLOAT
# =========================================================

def price_float(
    value: Any,
) -> Optional[float]:

    try:

        if value is None:

            return None

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# =========================================================
# SIGNAL VALUE
# =========================================================

def signal_value(
    signal,
    name: str,
    default=None,
):

    if isinstance(
        signal,
        dict,
    ):

        return signal.get(
            name,
            default
        )

    return getattr(
        signal,
        name,
        default
    )


# =========================================================
# ADD SIGNAL
# =========================================================

async def add_signal(
    signal,
):

    async with _monitor_lock:

        entry = price_float(
            signal_value(
                signal,
                "entry_price"
            )
        )

        sl = price_float(
            signal_value(
                signal,
                "sl"
            )
        )

        tp1 = price_float(
            signal_value(
                signal,
                "tp1"
            )
        )

        tp2 = price_float(
            signal_value(
                signal,
                "tp2"
            )
        )

        bias = str(
            signal_value(
                signal,
                "bias",
                ""
            )
        ).upper()

        # -------------------------------------------------
        # VALIDASI
        # -------------------------------------------------

        if (
            entry is None
            or sl is None
            or tp1 is None
        ):

            logger.error(
                "Signal invalid untuk monitor | "
                "entry=%s sl=%s tp1=%s",
                entry,
                sl,
                tp1,
            )

            return False

        # -------------------------------------------------
        # SIGNAL TIME
        # -------------------------------------------------

        signal_time = signal_value(
            signal,
            "signal_time"
        )

        signal_dt = parse_datetime(
            signal_time
        )

        if signal_dt is None:

            signal_dt = now_wib()

        # -------------------------------------------------
        # SIGNAL ID
        # -------------------------------------------------

        signal_id = signal_value(
            signal,
            "signal_id"
        )

        if signal_id is None:

            signal_id = (
                signal_dt.strftime(
                    "%Y%m%d%H%M"
                )
                + "_"
                + bias
            )

        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        for item in _active_signals:

            if item.get(
                "id"
            ) == signal_id:

                logger.warning(
                    "Signal sudah dimonitor: %s",
                    signal_id,
                )

                return False

        # -------------------------------------------------
        # CREATE
        # -------------------------------------------------

        monitor = {

            "id":
                signal_id,

            "signal":
                signal,

            "bias":
                bias,

            "entry":
                entry,

            "sl":
                sl,

            "tp1":
                tp1,

            "tp2":
                tp2,

            "signal_time":
                signal_dt,

            "status":
                "WAIT_ENTRY",

            "entry_hit":
                False,

            "entry_hit_time":
                None,

            "tp1_hit":
                False,

            "tp1_hit_time":
                None,

            "tp2_hit":
                False,

            "tp2_hit_time":
                None,

            "sl_hit":
                False,

            "sl_hit_time":
                None,

            "cancelled":
                False,

            "monitor_finished":
                False,

            "result_saved":
                False,

            "last_scan":
                None,

            "last_price":
                None,
        }

        _active_signals.append(
            monitor
        )

        logger.info(
            "MONITOR ADD | "
            "id=%s | bias=%s | "
            "entry=%s | tp1=%s | "
            "tp2=%s | sl=%s",
            signal_id,
            bias,
            entry,
            tp1,
            tp2,
            sl,
        )

        return True


# =========================================================
# SEND
# =========================================================

async def _send(
    bot,
    text: str,
):

    if bot is None:

        logger.error(
            "Bot tidak tersedia."
        )

        return

    try:

        await send_signal_to_members(
            bot,
            text,
        )

    except Exception:

        logger.exception(
            "Gagal mengirim monitor message."
        )


# =========================================================
# ENTRY TOUCHED
# =========================================================

def entry_touched(
    item,
    price: float,
):

    if item["bias"] == "BUY":

        return price <= item["entry"]

    if item["bias"] == "SELL":

        return price >= item["entry"]

    return False


# =========================================================
# TP1 TOUCHED
# =========================================================

def tp1_touched(
    item,
    price: float,
):

    if item["bias"] == "BUY":

        return price >= item["tp1"]

    if item["bias"] == "SELL":

        return price <= item["tp1"]

    return False


# =========================================================
# SL TOUCHED
# =========================================================

def sl_touched(
    item,
    price: float,
):

    if item["bias"] == "BUY":

        return price <= item["sl"]

    if item["bias"] == "SELL":

        return price >= item["sl"]

    return False


# =========================================================
# TP2 TOUCHED
# =========================================================

def tp2_touched(
    item,
    price: float,
):

    tp2 = item.get(
        "tp2"
    )

    if tp2 is None:

        return False

    if item["bias"] == "BUY":

        return price >= tp2

    if item["bias"] == "SELL":

        return price <= tp2

    return False


# =========================================================
# SAVE RESULT
# =========================================================

def save_result(
    item,
):

    if item.get(
        "result_saved"
    ):

        return

    try:

        save_signal_result(
            item
        )

        item["result_saved"] = True

    except Exception:

        logger.exception(
            "Gagal menyimpan performance | id=%s",
            item["id"],
        )


# =========================================================
# CANCEL ENTRY
# =========================================================

async def cancel_entry(
    bot,
    item,
):

    item["cancelled"] = True

    item["monitor_finished"] = True

    item["status"] = "CANCEL"

    save_result(
        item
    )

    text = (
        "❌ *SIGNAL CANCEL*\n"
        f"Entry `{item['entry']}` tidak tersentuh "
        f"dalam {ENTRY_TIMEOUT_MINUTES} menit."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# ENTRY HIT
# =========================================================

async def handle_entry_hit(
    bot,
    item,
):

    now = now_wib()

    item["entry_hit"] = True

    item["entry_hit_time"] = (
        now.isoformat()
    )

    item["status"] = (
        "MONITOR_TP1_SL"
    )

    text = (
        "🟢 *ENTRY TERSENTUH*\n"
        f"Entry `{item['entry']}`\n"
        "Monitoring TP1 & SL."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# TP1 HIT
# =========================================================

async def handle_tp1_hit(
    bot,
    item,
):

    now = now_wib()

    item["tp1_hit"] = True

    item["tp1_hit_time"] = (
        now.isoformat()
    )

    item["status"] = "TP1"

    # -----------------------------------------------------
    # SAVE PERFORMANCE
    # -----------------------------------------------------

    save_result(
        item
    )

    text = (
        "✅ *TP1 HIT*\n"
        "Profit +70 Pips.\n"
        "TP2 tanggung jawab masing-masing. "
        "Gunakan BE / SL Plus jika lanjut."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# SL HIT
# =========================================================

async def handle_sl_hit(
    bot,
    item,
):

    now = now_wib()

    item["sl_hit"] = True

    item["sl_hit_time"] = (
        now.isoformat()
    )

    item["status"] = "SL"

    item["monitor_finished"] = True

    save_result(
        item
    )

    text = (
        "❌ *SL HIT*\n"
        "Monitoring signal selesai."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# TP2 PORTFOLIO
# =========================================================

def handle_tp2_portfolio(
    item,
):

    if item.get(
        "tp2_hit"
    ):

        return

    item["tp2_hit"] = True

    item["tp2_hit_time"] = (
        now_wib().isoformat()
    )

    logger.info(
        "TP2 HIT | PORTFOLIO ONLY | id=%s",
        item["id"],
    )

    # -----------------------------------------------------
    # UPDATE PERFORMANCE
    # -----------------------------------------------------

    save_result(
        item
    )


# =========================================================
# END :59
# =========================================================

async def finish_at_minute_59(
    bot,
    item,
):

    item["monitor_finished"] = True

    item["status"] = "TIMEOUT"

    save_result(
        item
    )

    signal_time = item[
        "signal_time"
    ]

    text = (
        f"⏹️ *Monitoring Signal "
        f"{signal_time.strftime('%H:%M')} "
        f"diakhiri.*\n"
        "1 menit lagi signal baru akan keluar.\n"
        "Semoga entry kita segera menyentuh TP."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# PROCESS
# =========================================================

async def process_signal(
    bot,
    item,
    price: float,
):

    now = now_wib()

    item["last_scan"] = (
        now.isoformat()
    )

    item["last_price"] = price

    # =====================================================
    # TP2 PORTFOLIO
    # =====================================================

    if (
        item.get("entry_hit")
        and not item.get("tp2_hit")
    ):

        if tp2_touched(
            item,
            price,
        ):

            handle_tp2_portfolio(
                item
            )

    # =====================================================
    # FINISHED
    # =====================================================

    if item.get(
        "monitor_finished"
    ):

        return

    # =====================================================
    # ENTRY BELUM HIT
    # =====================================================

    if not item.get(
        "entry_hit"
    ):

        # -------------------------------------------------
        # ENTRY
        # -------------------------------------------------

        if entry_touched(
            item,
            price,
        ):

            await handle_entry_hit(
                bot,
                item,
            )

            return

        # -------------------------------------------------
        # TIMEOUT 20 MENIT
        # -------------------------------------------------

        elapsed = (
            now
            - item["signal_time"]
        ).total_seconds() / 60

        if elapsed >= ENTRY_TIMEOUT_MINUTES:

            await cancel_entry(
                bot,
                item,
            )

            return

        logger.info(
            "WAIT ENTRY | id=%s | "
            "price=%s | entry=%s | "
            "elapsed=%.1f",
            item["id"],
            price,
            item["entry"],
            elapsed,
        )

        return

    # =====================================================
    # SETELAH ENTRY
    # =====================================================

    # -----------------------------------------------------
    # :59
    # -----------------------------------------------------

    if now.minute >= MONITOR_END_MINUTE:

        await finish_at_minute_59(
            bot,
            item,
        )

        return

    # -----------------------------------------------------
    # TP1 SUDAH HIT
    #
    # Setelah TP1:
    # SL TIDAK BOLEH menjadi LOSS.
    # TP2 hanya portfolio.
    # -----------------------------------------------------

    if item.get(
        "tp1_hit"
    ):

        return

    # -----------------------------------------------------
    # SL
    # -----------------------------------------------------

    if sl_touched(
        item,
        price,
    ):

        await handle_sl_hit(
            bot,
            item,
        )

        return

    # -----------------------------------------------------
    # TP1
    # -----------------------------------------------------

    if tp1_touched(
        item,
        price,
    ):

        await handle_tp1_hit(
            bot,
            item,
        )

        return

    logger.info(
        "MONITOR | id=%s | "
        "price=%s | tp1=%s | sl=%s",
        item["id"],
        price,
        item["tp1"],
        item["sl"],
    )


# =========================================================
# SCAN
# =========================================================

async def scan(
    bot,
):

    if not _active_signals:

        return

    # -----------------------------------------------------
    # GET PRICE
    # -----------------------------------------------------

    price = await asyncio.to_thread(
        get_price
    )

    if price is None:

        logger.warning(
            "Monitor gagal mendapatkan harga."
        )

        return

    logger.info(
        "MONITOR SCAN | price=%s | active=%s",
        price,
        len(
            _active_signals
        ),
    )

    # -----------------------------------------------------
    # PROCESS
    # -----------------------------------------------------

    async with _monitor_lock:

        for item in list(
            _active_signals
        ):

            try:

                await process_signal(
                    bot,
                    item,
                    price,
                )

            except Exception:

                logger.exception(
                    "Monitor error | id=%s",
                    item.get("id"),
                )

        # -------------------------------------------------
        # REMOVE
        # -------------------------------------------------

        remove_finished()


# =========================================================
# REMOVE FINISHED
# =========================================================

def remove_finished():

    global _active_signals

    before = len(
        _active_signals
    )

    _active_signals = [

        item

        for item in _active_signals

        if not item.get(
            "monitor_finished",
            False,
        )

    ]

    removed = (
        before
        - len(
            _active_signals
        )
    )

    if removed:

        logger.info(
            "Monitor selesai: %s signal",
            removed,
        )


# =========================================================
# MONITOR LOOP
# =========================================================

async def monitor_loop(
    bot,
):

    logger.info(
        "=========================================="
    )

    logger.info(
        "XAU AI MONITOR ACTIVE"
    )

    logger.info(
        "Scan interval : 5 menit"
    )

    logger.info(
        "Entry timeout : 20 menit"
    )

    logger.info(
        "TP1 / SL end  : menit :59"
    )

    logger.info(
        "TP2           : PORTFOLIO ONLY"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            await scan(
                bot
            )

        except asyncio.CancelledError:

            logger.info(
                "Monitor dihentikan."
            )

            raise

        except Exception:

            logger.exception(
                "Monitor loop error."
            )

        await asyncio.sleep(
            MONITOR_INTERVAL_MINUTES * 60
        )


# =========================================================
# ACTIVE MONITORS
# =========================================================

def get_active_monitors():

    return list(
        _active_signals
    )
