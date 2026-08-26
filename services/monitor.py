"""
services/monitor.py

XAU AI SIGNAL MONITOR
=====================

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


MONITOR:

- Scan setiap 5 menit
- Menggunakan candle 5 menit
- HIGH / LOW digunakan untuk mendeteksi TP1 / SL
- Entry maksimal ditunggu 20 menit
- TP1 = hasil Performance
- SL  = hasil Performance
- TP2 = internal / tanggung jawab masing-masing user
- TP2 tidak dikirim sebagai hasil Performance
- Monitoring berhenti pada menit :59
"""

import asyncio
import logging

from datetime import datetime
from typing import Any, Dict, List, Optional


from config.settings import TIMEZONE

from services.market import (
    get_price,
    get_candles,
)

from services.sender import (
    send_signal_to_members,
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
    "signal_monitor"
)


# =========================================================
# CONFIG
# =========================================================

# Scan monitor setiap 5 menit
MONITOR_INTERVAL_MINUTES = 5

# Entry maksimal ditunggu 20 menit
ENTRY_TIMEOUT_MINUTES = 20

# Monitoring berhenti pada menit 59
MONITOR_END_MINUTE = 59

# Candle yang digunakan untuk verifikasi
MONITOR_CANDLE_INTERVAL = "5min"


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

async def add_signal(
    signal,
):

    async with _monitor_lock:

        # =================================================
        # SIGNAL VALUES
        # =================================================

        entry = price_float(
            signal_value(
                signal,
                "entry_price",
            )
        )

        sl = price_float(
            signal_value(
                signal,
                "sl",
            )
        )

        tp1 = price_float(
            signal_value(
                signal,
                "tp1",
            )
        )

        tp2 = price_float(
            signal_value(
                signal,
                "tp2",
            )
        )

        bias = str(
            signal_value(
                signal,
                "bias",
                "",
            )
        ).upper()

        # =================================================
        # VALIDATION
        # =================================================

        if (
            entry is None
            or sl is None
            or tp1 is None
        ):

            logger.error(
                "Signal tidak valid untuk monitor | "
                "entry=%s | sl=%s | tp1=%s",
                entry,
                sl,
                tp1,
            )

            return False

        if bias not in (
            "BUY",
            "SELL",
        ):

            logger.error(
                "Bias signal tidak valid: %s",
                bias,
            )

            return False

        # =================================================
        # SIGNAL TIME
        # =================================================

        signal_time = signal_value(
            signal,
            "signal_time",
        )

        signal_dt = parse_datetime(
            signal_time
        )

        if signal_dt is None:

            signal_dt = now_wib()

        # =================================================
        # SIGNAL ID
        # =================================================

        signal_id = signal_value(
            signal,
            "signal_id",
        )

        if signal_id is None:

            signal_id = (
                signal_dt.strftime(
                    "%Y%m%d%H%M"
                )
                + "_"
                + bias
            )

        # =================================================
        # DUPLICATE
        # =================================================

        for item in _active_signals:

            if item.get(
                "id"
            ) == signal_id:

                logger.warning(
                    "Signal sudah dimonitor: %s",
                    signal_id,
                )

                return False

        # =================================================
        # CREATE MONITOR
        # =================================================

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

            # ---------------------------------------------
            # STATUS
            # ---------------------------------------------

            "status":
                "WAIT_ENTRY",

            # ---------------------------------------------
            # ENTRY
            # ---------------------------------------------

            "entry_hit":
                False,

            "entry_hit_time":
                None,

            # ---------------------------------------------
            # TP1
            # ---------------------------------------------

            "tp1_hit":
                False,

            "tp1_hit_time":
                None,

            # ---------------------------------------------
            # SL
            # ---------------------------------------------

            "sl_hit":
                False,

            "sl_hit_time":
                None,

            # ---------------------------------------------
            # TP2
            # ---------------------------------------------

            "tp2_hit":
                False,

            "tp2_hit_time":
                None,

            # ---------------------------------------------
            # FINISH
            # ---------------------------------------------

            "monitor_finished":
                False,

            "cancelled":
                False,

            # ---------------------------------------------
            # SCAN
            # ---------------------------------------------

            "last_scan":
                None,

            "last_price":
                None,

            "last_candle_time":
                None,

            # ---------------------------------------------
            # PERFORMANCE RESULT
            # ---------------------------------------------

            "performance_result":
                None,

            "performance_time":
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
    item: Dict[str, Any],
    price: float,
) -> bool:

    entry = item[
        "entry"
    ]

    bias = item[
        "bias"
    ]

    if bias == "BUY":

        return price <= entry

    if bias == "SELL":

        return price >= entry

    return False


# =========================================================
# ENTRY TOUCHED BY CANDLE
# =========================================================

def entry_touched_by_candle(
    item: Dict[str, Any],
    candle: Dict[str, Any],
) -> bool:

    entry = item[
        "entry"
    ]

    high = price_float(
        candle.get(
            "high"
        )
    )

    low = price_float(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    # ---------------------------------------------
    # Entry akan dianggap tersentuh apabila
    # harga entry berada di dalam range candle.
    # ---------------------------------------------

    return (
        low <= entry <= high
    )


# =========================================================
# TP1 BY CANDLE
# =========================================================

def tp1_touched_by_candle(
    item: Dict[str, Any],
    candle: Dict[str, Any],
) -> bool:

    tp1 = item[
        "tp1"
    ]

    high = price_float(
        candle.get(
            "high"
        )
    )

    low = price_float(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    bias = item[
        "bias"
    ]

    if bias == "BUY":

        return high >= tp1

    if bias == "SELL":

        return low <= tp1

    return False


# =========================================================
# SL BY CANDLE
# =========================================================

def sl_touched_by_candle(
    item: Dict[str, Any],
    candle: Dict[str, Any],
) -> bool:

    sl = item[
        "sl"
    ]

    high = price_float(
        candle.get(
            "high"
        )
    )

    low = price_float(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    bias = item[
        "bias"
    ]

    if bias == "BUY":

        return low <= sl

    if bias == "SELL":

        return high >= sl

    return False


# =========================================================
# TP2 BY CANDLE
# =========================================================

def tp2_touched_by_candle(
    item: Dict[str, Any],
    candle: Dict[str, Any],
) -> bool:

    tp2 = item.get(
        "tp2"
    )

    if tp2 is None:

        return False

    high = price_float(
        candle.get(
            "high"
        )
    )

    low = price_float(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    bias = item[
        "bias"
    ]

    if bias == "BUY":

        return high >= tp2

    if bias == "SELL":

        return low <= tp2

    return False


# =========================================================
# CANCEL ENTRY
# =========================================================

async def cancel_entry(
    bot,
    item: Dict[str, Any],
):

    item[
        "cancelled"
    ] = True

    item[
        "monitor_finished"
    ] = True

    item[
        "status"
    ] = "CANCEL"

    item[
        "performance_result"
    ] = "CANCEL"

    item[
        "performance_time"
    ] = now_wib().isoformat()

    logger.info(
        "ENTRY CANCEL | "
        "id=%s | "
        "entry=%s",
        item["id"],
        item["entry"],
    )

    text = (
        "❌ *SIGNAL CANCEL*\n"
        f"Entry `{item['entry']}` tidak tersentuh "
        f"dalam {ENTRY_TIMEOUT_MINUTES} menit.\n\n"
        "Signal tidak masuk posisi."
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

    item[
        "entry_hit"
    ] = True

    item[
        "entry_hit_time"
    ] = now.isoformat()

    item[
        "status"
    ] = "MONITOR_TP1_SL"

    logger.info(
        "ENTRY HIT | "
        "id=%s | "
        "entry=%s",
        item["id"],
        item["entry"],
    )

    text = (
        "🟢 *ENTRY TERSENTUH*\n"
        f"Entry `{item['entry']}`\n\n"
        "Posisi mulai dimonitor.\n"
        "🎯 TP1 dan 🛑 SL sedang dipantau."
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

    item[
        "tp1_hit"
    ] = True

    item[
        "tp1_hit_time"
    ] = now.isoformat()

    item[
        "status"
    ] = "TP1"

    item[
        "performance_result"
    ] = "TP1"

    item[
        "performance_time"
    ] = now.isoformat()

    logger.info(
        "TP1 HIT | "
        "id=%s | "
        "tp1=%s",
        item["id"],
        item["tp1"],
    )

    text = (
        "✅ *TP1 HIT*\n"
        "Profit +70 Pips\n\n"
        "🎯 TP1 sudah tercapai.\n\n"
        "⚠️ *TP2 menjadi tanggung jawab "
        "masing-masing user.*\n"
        "Jika posisi masih dilanjutkan, "
        "silakan amankan posisi menggunakan "
        "BE / SL Plus sesuai manajemen risiko "
        "masing-masing."
    )

    await _send(
        bot,
        text,
    )

    # -----------------------------------------------------
    # Setelah TP1:
    #
    # Performance sudah FINAL = TP1.
    #
    # SL berikutnya TIDAK mengubah hasil
    # menjadi SL.
    #
    # TP2 hanya dicatat internal.
    # -----------------------------------------------------

    item[
        "status"
    ] = "MONITOR_TP2"


# =========================================================
# SL HIT
# =========================================================

async def handle_sl_hit(
    bot,
    item: Dict[str, Any],
):

    now = now_wib()

    item[
        "sl_hit"
    ] = True

    item[
        "sl_hit_time"
    ] = now.isoformat()

    item[
        "status"
    ] = "SL"

    item[
        "performance_result"
    ] = "SL"

    item[
        "performance_time"
    ] = now.isoformat()

    item[
        "monitor_finished"
    ] = True

    logger.info(
        "SL HIT | "
        "id=%s | "
        "sl=%s",
        item["id"],
        item["sl"],
    )

    text = (
        "❌ *SL HIT*\n"
        "Loss sesuai risk management.\n\n"
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

    item[
        "tp2_hit"
    ] = True

    item[
        "tp2_hit_time"
    ] = now_wib().isoformat()

    logger.info(
        "TP2 HIT | "
        "PORTFOLIO ONLY | "
        "id=%s | "
        "tp2=%s",
        item["id"],
        item["tp2"],
    )


# =========================================================
# END :59
# =========================================================

async def finish_at_minute_59(
    bot,
    item: Dict[str, Any],
):

    now = now_wib()

    item[
        "monitor_finished"
    ] = True

    item[
        "status"
    ] = "TIMEOUT"

    # -----------------------------------------------------
    # Jika belum ada hasil Performance:
    # -----------------------------------------------------

    if not item.get(
        "performance_result"
    ):

        item[
            "performance_result"
        ] = "TIMEOUT"

        item[
            "performance_time"
        ] = now.isoformat()

    logger.info(
        "MONITOR END :59 | "
        "id=%s | "
        "result=%s",
        item["id"],
        item.get(
            "performance_result"
        ),
    )

    text = (
        f"⏹️ *Monitoring Signal "
        f"{item['signal_time'].strftime('%H:%M')} "
        f"diakhiri.*\n\n"
        "1 menit lagi signal baru akan keluar.\n"
        "Semoga entry kita saat ini "
        "segera menyentuh TP."
    )

    await _send(
        bot,
        text,
    )


# =========================================================
# PROCESS CANDLE
# =========================================================

async def process_candle(
    bot,
    item: Dict[str, Any],
    candle: Dict[str, Any],
):

    now = now_wib()

    item[
        "last_scan"
    ] = now.isoformat()

    candle_time = candle.get(
        "datetime"
    )

    item[
        "last_candle_time"
    ] = str(
        candle_time
    )

    # =====================================================
    # CANDLE VALUES
    # =====================================================

    high = price_float(
        candle.get(
            "high"
        )
    )

    low = price_float(
        candle.get(
            "low"
        )
    )

    close = price_float(
        candle.get(
            "close"
        )
    )

    if (
        high is None
        or low is None
        or close is None
    ):

        logger.warning(
            "Candle tidak valid | %s",
            candle,
        )

        return

    item[
        "last_price"
    ] = close

    # =====================================================
    # TP2 INTERNAL
    # =====================================================

    if (
        item.get(
            "entry_hit"
        )
        and
        not item.get(
            "tp2_hit"
        )
    ):

        if tp2_touched_by_candle(
            item,
            candle,
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

        if entry_touched_by_candle(
            item,
            candle,
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
            "WAIT ENTRY | "
            "id=%s | "
            "candle=%s | "
            "high=%s | "
            "low=%s | "
            "entry=%s | "
            "elapsed=%.1f min",
            item["id"],
            candle_time,
            high,
            low,
            item["entry"],
            elapsed,
        )

        return

    # =====================================================
    # ENTRY SUDAH HIT
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

    # =====================================================
    # TP1 / SL
    # =====================================================

    tp1_hit = False

    sl_hit = False

    # -----------------------------------------------------
    # SL
    # -----------------------------------------------------

    if not item.get(
        "tp1_hit"
    ):

        sl_hit = sl_touched_by_candle(
            item,
            candle,
        )

        tp1_hit = tp1_touched_by_candle(
            item,
            candle,
        )

        # -------------------------------------------------
        # Jika TP1 dan SL sama-sama kena dalam candle
        # yang sama, kita TIDAK bisa tahu urutannya.
        #
        # Conservative rule:
        # SL diprioritaskan.
        # -------------------------------------------------

        if (
            sl_hit
            and
            tp1_hit
        ):

            logger.warning(
                "TP1 + SL SAMA-SAMA tersentuh "
                "dalam candle yang sama | "
                "id=%s | "
                "SL diprioritaskan.",
                item["id"],
            )

            await handle_sl_hit(
                bot,
                item,
            )

            return

        # -------------------------------------------------
        # SL ONLY
        # -------------------------------------------------

        if sl_hit:

            await handle_sl_hit(
                bot,
                item,
            )

            return

        # -------------------------------------------------
        # TP1 ONLY
        # -------------------------------------------------

        if tp1_hit:

            await handle_tp1_hit(
                bot,
                item,
            )

            return

    # =====================================================
    # SETELAH TP1
    # =====================================================

    if item.get(
        "tp1_hit"
    ):

        # -------------------------------------------------
        # TP2 hanya dicatat.
        #
        # SL TIDAK BOLEH mengubah hasil Performance.
        # -------------------------------------------------

        logger.info(
            "TP1 SUDAH HIT | "
            "Monitoring publik selesai | "
            "TP2 internal | "
            "id=%s",
            item["id"],
        )

        return

    # =====================================================
    # BELUM ADA HASIL
    # =====================================================

    logger.info(
        "MONITOR | "
        "id=%s | "
        "candle=%s | "
        "high=%s | "
        "low=%s | "
        "tp1=%s | "
        "sl=%s",
        item["id"],
        candle_time,
        high,
        low,
        item["tp1"],
        item["sl"],
    )


# =========================================================
# GET MONITOR CANDLE
# =========================================================

def get_monitor_candle():

    try:

        candles = get_candles(
            interval=MONITOR_CANDLE_INTERVAL,
            outputsize=2,
        )

    except Exception:

        logger.exception(
            "Gagal mengambil candle monitor."
        )

        return None

    if not candles:

        return None

    # -----------------------------------------------------
    # Ambil candle terbaru.
    # -----------------------------------------------------

    candle = candles[-1]

    return candle


# =========================================================
# SCAN
# =========================================================

async def scan(
    bot,
):

    if not _active_signals:

        return

    # =====================================================
    # GET CANDLE
    # =====================================================

    candle = await asyncio.to_thread(
        get_monitor_candle
    )

    if candle is None:

        logger.warning(
            "Monitor tidak mendapatkan "
            "candle 5 menit."
        )

        return

    # =====================================================
    # GET PRICE
    # =====================================================

    price = await asyncio.to_thread(
        get_price
    )

    if price is None:

        price = price_float(
            candle.get(
                "close"
            )
        )

    if price is None:

        logger.warning(
            "Monitor tidak mendapatkan harga."
        )

        return

    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "MONITOR SCAN | "
        "price=%s | "
        "candle=%s | "
        "high=%s | "
        "low=%s | "
        "active=%s",
        price,
        candle.get(
            "datetime"
        ),
        candle.get(
            "high"
        ),
        candle.get(
            "low"
        ),
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

                await process_candle(
                    bot,
                    item,
                    candle,
                )

            except Exception:

                logger.exception(
                    "Monitor error | "
                    "id=%s",
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
        "Candle        : %s",
        MONITOR_CANDLE_INTERVAL,
    )

    logger.info(
        "TP1           : PERFORMANCE"
    )

    logger.info(
        "SL            : PERFORMANCE"
    )

    logger.info(
        "TP2           : USER RESPONSIBILITY"
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
        # WAIT 5 MINUTES
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
# GET FINISHED DATA
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
