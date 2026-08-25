"""
services/monitor.py

XAU AI SIGNAL MONITOR
=====================

Fungsi:

1. Monitor pending entry
2. Entry maksimal ditunggu 20 menit
3. Jika entry tidak tersentuh -> CANCEL
4. Jika entry tersentuh -> monitor TP1 + SL
5. TP1 dan SL dikirim ke Telegram
6. TP2 hanya dicatat untuk portfolio
7. Monitoring berhenti pada menit :59
8. Scan harga setiap 10 menit
9. Tidak spam Telegram jika belum ada perubahan

FLOW:

SIGNAL
  |
  v
WAIT ENTRY
  |
  +-- ENTRY HIT ------> MONITOR TP1 / SL
  |
  +-- 20 MENIT -------> CANCEL
                         |
                         v
                    SIGNAL SELESAI

ENTRY HIT
  |
  +-- TP1 HIT ---------> PROFIT
  |
  +-- SL HIT ----------> LOSS
  |
  +-- :59 -------------> END MONITORING

TP2:

Tidak dikirim sebagai alert monitoring.

Tetap dicatat untuk portfolio.
"""

import asyncio
import logging

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import TIMEZONE

from services.market import get_price
from services.sender import send_signal_to_members


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

# Scan setiap 10 menit
MONITOR_INTERVAL_MINUTES = 10

# Entry maksimal ditunggu 20 menit
ENTRY_TIMEOUT_MINUTES = 20

# Monitoring TP1 / SL berhenti pada menit 59
MONITOR_END_MINUTE = 59


# =========================================================
# ACTIVE SIGNALS
# =========================================================

_active_signals: List[Dict[str, Any]] = []


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
# NORMALIZE PRICE
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
# GET SIGNAL VALUE
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
    """
    Menambahkan signal baru ke monitor.

    Signal yang masuk langsung masuk status:

        WAIT_ENTRY
    """

    async with _monitor_lock:

        # -------------------------------------------------
        # SIGNAL DATA
        # -------------------------------------------------

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
                "Signal tidak valid untuk monitor | "
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
        # UNIQUE ID
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
        # CREATE MONITOR
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

            "sl_hit":
                False,

            "sl_hit_time":
                None,

            "tp2_hit":
                False,

            "tp2_hit_time":
                None,

            "monitor_finished":
                False,

            "cancelled":
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
            "id=%s | "
            "bias=%s | "
            "entry=%s | "
            "sl=%s | "
            "tp1=%s | "
            "tp2=%s",
            signal_id,
            bias,
            entry,
            sl,
            tp1,
            tp2,
        )

        return True


# =========================================================
# REMOVE FINISHED SIGNAL
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
            False
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
# SEND MESSAGE
# =========================================================

async def _send(
    bot,
    text: str,
):

    if bot is None:

        logger.error(
            "Bot tidak tersedia untuk monitor."
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
# CHECK ENTRY
# =========================================================

def entry_touched(
    item: Dict[str, Any],
    price: float,
) -> bool:

    entry = item["entry"]

    bias = item["bias"]

    # -----------------------------------------------------
    # BUY
    # -----------------------------------------------------

    if bias == "BUY":

        return price <= entry

    # -----------------------------------------------------
    # SELL
    # -----------------------------------------------------

    if bias == "SELL":

        return price >= entry

    return False


# =========================================================
# CHECK TP1
# =========================================================

def tp1_touched(
    item: Dict[str, Any],
    price: float,
) -> bool:

    tp1 = item["tp1"]

    bias = item["bias"]

    # BUY -> harga naik ke TP
    if bias == "BUY":

        return price >= tp1

    # SELL -> harga turun ke TP
    if bias == "SELL":

        return price <= tp1

    return False


# =========================================================
# CHECK SL
# =========================================================

def sl_touched(
    item: Dict[str, Any],
    price: float,
) -> bool:

    sl = item["sl"]

    bias = item["bias"]

    # BUY -> SL di bawah
    if bias == "BUY":

        return price <= sl

    # SELL -> SL di atas
    if bias == "SELL":

        return price >= sl

    return False


# =========================================================
# CHECK TP2
# =========================================================

def tp2_touched(
    item: Dict[str, Any],
    price: float,
) -> bool:

    tp2 = item["tp2"]

    if tp2 is None:

        return False

    bias = item["bias"]

    if bias == "BUY":

        return price >= tp2

    if bias == "SELL":

        return price <= tp2

    return False


# =========================================================
# ENTRY CANCEL
# =========================================================

async def cancel_entry(
    bot,
    item: Dict[str, Any],
):

    item["cancelled"] = True

    item["monitor_finished"] = True

    item["status"] = "CANCEL"

    logger.info(
        "ENTRY CANCEL | id=%s | entry=%s",
        item["id"],
        item["entry"],
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
    item: Dict[str, Any],
):

    now = now_wib()

    item["entry_hit"] = True

    item["entry_hit_time"] = (
        now.isoformat()
    )

    item["status"] = "MONITOR_TP1_SL"

    logger.info(
        "ENTRY HIT | id=%s | price=%s",
        item["id"],
        item["last_price"],
    )

    text = (
        "🟢 *ENTRY TERSENTUH*\n"
        f"Entry `{item['entry']}`\n"
        "Monitoring TP1 & SL dimulai."
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
    item: Dict[str, Any],
):

    now = now_wib()

    item["tp1_hit"] = True

    item["tp1_hit_time"] = (
        now.isoformat()
    )

    item["status"] = "TP1"

    logger.info(
        "TP1 HIT | id=%s | tp1=%s",
        item["id"],
        item["tp1"],
    )

    text = (
        "✅ *TP1 HIT*\n"
        "Profit +70 Pips\n\n"
        "TP2 menjadi tanggung jawab masing-masing.\n"
        "Jika lanjut, gunakan BE / SL Plus."
    )

    await _send(
        bot,
        text,
    )

    # -----------------------------------------------------
    # TP1 sudah selesai untuk monitoring publik.
    #
    # TP2 tetap dicari untuk portfolio.
    # -----------------------------------------------------

    item["status"] = "MONITOR_TP2_PORTFOLIO"


# =========================================================
# SL HIT
# =========================================================

async def handle_sl_hit(
    bot,
    item: Dict[str, Any],
):

    now = now_wib()

    item["sl_hit"] = True

    item["sl_hit_time"] = (
        now.isoformat()
    )

    item["status"] = "SL"

    item["monitor_finished"] = True

    logger.info(
        "SL HIT | id=%s | sl=%s",
        item["id"],
        item["sl"],
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
    item: Dict[str, Any],
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
        "TP2 HIT | PORTFOLIO ONLY | "
        "id=%s | tp2=%s",
        item["id"],
        item["tp2"],
    )


# =========================================================
# END AT :59
# =========================================================

async def finish_at_minute_59(
    bot,
    item: Dict[str, Any],
):

    now = now_wib()

    item["monitor_finished"] = True

    item["status"] = "TIMEOUT"

    logger.info(
        "MONITOR END :59 | id=%s",
        item["id"],
    )

    text = (
        f"⏹️ *Monitoring Signal "
        f"{item['signal_time'].strftime('%H:%M')} "
        f"diakhiri.*\n"
        "1 menit lagi signal baru akan keluar.\n"
        "Semoga entry kita segera menyentuh TP."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# PROCESS ONE SIGNAL
# =========================================================

async def process_signal(
    bot,
    item: Dict[str, Any],
    price: float,
):

    now = now_wib()

    item["last_scan"] = (
        now.isoformat()
    )

    item["last_price"] = price

    signal_time = item["signal_time"]

    elapsed = (
        now - signal_time
    ).total_seconds() / 60

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
    # SUDAH FINISH
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
        # CHECK ENTRY
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
        # 20 MINUTE TIMEOUT
        # -------------------------------------------------

        if elapsed >= ENTRY_TIMEOUT_MINUTES:

            await cancel_entry(
                bot,
                item,
            )

            return

        # -------------------------------------------------
        # BELUM KENA
        # -------------------------------------------------

        logger.info(
            "WAIT ENTRY | "
            "id=%s | "
            "price=%s | "
            "entry=%s | "
            "elapsed=%.1f min",
            item["id"],
            price,
            item["entry"],
            elapsed,
        )

        return

    # =====================================================
    # ENTRY SUDAH HIT
    # =====================================================

    # -----------------------------------------------------
    # :59 END MONITORING TP1/SL
    # -----------------------------------------------------

    if now.minute >= MONITOR_END_MINUTE:

        await finish_at_minute_59(
            bot,
            item,
        )

        return

    # =====================================================
    # TP1 / SL
    # =====================================================

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

    if (
        not item.get(
            "tp1_hit"
        )
        and
        tp1_touched(
            item,
            price,
        )
    ):

        await handle_tp1_hit(
            bot,
            item,
        )

        return

    # -----------------------------------------------------
    # BELUM KENA
    # -----------------------------------------------------

    logger.info(
        "MONITOR TP1/SL | "
        "id=%s | "
        "price=%s | "
        "tp1=%s | "
        "sl=%s",
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

    # =====================================================
    # GET PRICE
    # =====================================================

    price = await asyncio.to_thread(
        get_price
    )

    if price is None:

        logger.warning(
            "Monitor tidak mendapatkan harga."
        )

        return

    logger.info(
        "MONITOR SCAN | price=%s | active=%s",
        price,
        len(
            _active_signals
        ),
    )

    # =====================================================
    # PROCESS
    # =====================================================

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
                    item.get(
                        "id"
                    ),
                )

        # -------------------------------------------------
        # REMOVE FINISHED
        # -------------------------------------------------

        remove_finished()


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
        "Scan interval : %s menit",
        MONITOR_INTERVAL_MINUTES,
    )

    logger.info(
        "Entry timeout : %s menit",
        ENTRY_TIMEOUT_MINUTES,
    )

    logger.info(
        "TP1 / SL end  : menit :%s",
        MONITOR_END_MINUTE,
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

        # =================================================
        # WAIT 10 MINUTES
        # =================================================

        await asyncio.sleep(
            MONITOR_INTERVAL_MINUTES
            * 60
        )


# =========================================================
# GET ACTIVE
# =========================================================

def get_active_monitors():

    return list(
        _active_signals
    )


# =========================================================
# GET PORTFOLIO DATA
# =========================================================

def get_finished_data():

    return [

        item

        for item in _active_signals

        if (
            item.get(
                "tp1_hit"
            )
            or
            item.get(
                "sl_hit"
            )
            or
            item.get(
                "tp2_hit"
            )
            or
            item.get(
                "cancelled"
            )
        )

    ]
