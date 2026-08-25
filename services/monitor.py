"""
services/monitor.py

XAU AI SIGNAL MONITOR

Fungsi:

1. Monitor pending ENTRY
   maksimal 20 menit.

2. Jika ENTRY tersentuh:
   - kirim notifikasi ENTRY
   - mulai monitoring TP1 / SL

3. TP1 / SL:
   - disiarkan ke Telegram

4. TP2:
   - TIDAK disiarkan
   - hanya dicatat ke portfolio

5. Jika ENTRY tidak tersentuh 20 menit:
   - CANCEL
   - kirim notifikasi CANCEL

6. Pada menit 59:
   - jika TP1 / SL belum kena
   - akhiri monitoring broadcast
   - kirim pesan penutupan

7. API:
   - scan sekitar 10 menit sekali
   - tidak scan setiap detik
"""

import asyncio
import logging

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from config.settings import TIMEZONE

from services.market import get_price

from services.portfolio import (
    add_signal,
    update_signal,
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

# Scan market setiap 10 menit.
MONITOR_INTERVAL_SECONDS = 600


# ENTRY maksimal menunggu 20 menit.
ENTRY_TIMEOUT_MINUTES = 20


# Signal aktif maksimal sampai menit 59.
MAX_SIGNAL_MINUTES = 59


# =========================================================
# STATE
# =========================================================

@dataclass
class MonitorItem:

    # ID internal monitor
    monitor_id: str

    # Signal object asli
    signal: Any

    # Waktu signal dibuat
    signal_time: datetime

    # Waktu terakhir scan
    last_scan: Optional[datetime] = None

    # ENTRY sudah tersentuh
    entry_hit: bool = False

    # TP1 sudah kena
    tp1_hit: bool = False

    # TP2 sudah kena
    tp2_hit: bool = False

    # SL sudah kena
    sl_hit: bool = False

    # Signal dibatalkan
    cancelled: bool = False

    # Monitoring broadcast selesai
    monitoring_finished: bool = False

    # Portfolio ID
    portfolio_id: Optional[str] = None


# =========================================================
# GLOBAL MONITOR
# =========================================================

_active_monitors: Dict[
    str,
    MonitorItem
] = {}


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
# SIGNAL VALUE
# =========================================================

def _get(
    signal,
    name: str,
    default=None,
):

    return getattr(
        signal,
        name,
        default,
    )


# =========================================================
# DIRECTION
# =========================================================

def get_direction(
    signal,
) -> str:

    direction = _get(
        signal,
        "bias",
        None,
    )

    if direction is None:

        direction = _get(
            signal,
            "direction",
            "",
        )

    return str(
        direction
    ).upper()


# =========================================================
# ENTRY
# =========================================================

def get_entry(
    signal,
) -> Optional[float]:

    value = _get(
        signal,
        "entry_price",
        None,
    )

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# =========================================================
# TP1
# =========================================================

def get_tp1(
    signal,
) -> Optional[float]:

    value = _get(
        signal,
        "tp1",
        None,
    )

    if value is None:

        value = _get(
            signal,
            "tp1_price",
            None,
        )

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# =========================================================
# TP2
# =========================================================

def get_tp2(
    signal,
) -> Optional[float]:

    value = _get(
        signal,
        "tp2",
        None,
    )

    if value is None:

        value = _get(
            signal,
            "tp2_price",
            None,
        )

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# =========================================================
# SL
# =========================================================

def get_sl(
    signal,
) -> Optional[float]:

    value = _get(
        signal,
        "sl",
        None,
    )

    if value is None:

        value = _get(
            signal,
            "sl_price",
            None,
        )

    try:

        return float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None


# =========================================================
# SIGNAL TIME
# =========================================================

def get_signal_time(
    signal,
) -> datetime:

    value = _get(
        signal,
        "signal_time",
        None,
    )

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

        except Exception:

            dt = now_wib()

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
# UNIQUE MONITOR ID
# =========================================================

def build_monitor_id(
    signal,
) -> str:

    signal_time = get_signal_time(
        signal
    )

    entry = get_entry(
        signal
    )

    direction = get_direction(
        signal
    )

    return (
        signal_time.strftime(
            "%Y%m%d_%H%M"
        )
        + "_"
        + direction
        + "_"
        + str(entry)
    )


# =========================================================
# PRICE HIT ENTRY
# =========================================================

def entry_hit(
    signal,
    price: float,
) -> bool:

    entry = get_entry(
        signal
    )

    if entry is None:

        return False

    # -----------------------------------------------------
    # BUY
    #
    # Harga menyentuh entry jika:
    #
    # price <= entry
    #
    # -----------------------------------------------------

    direction = get_direction(
        signal
    )

    if direction in (
        "BUY",
        "LONG",
    ):

        return price <= entry

    # -----------------------------------------------------
    # SELL
    #
    # Harga menyentuh entry jika:
    #
    # price >= entry
    #
    # -----------------------------------------------------

    if direction in (
        "SELL",
        "SHORT",
    ):

        return price >= entry

    return False


# =========================================================
# PRICE HIT TP1
# =========================================================

def tp1_hit(
    signal,
    price: float,
) -> bool:

    tp1 = get_tp1(
        signal
    )

    if tp1 is None:

        return False

    direction = get_direction(
        signal
    )

    if direction in (
        "BUY",
        "LONG",
    ):

        return price >= tp1

    if direction in (
        "SELL",
        "SHORT",
    ):

        return price <= tp1

    return False


# =========================================================
# PRICE HIT TP2
# =========================================================

def tp2_hit(
    signal,
    price: float,
) -> bool:

    tp2 = get_tp2(
        signal
    )

    if tp2 is None:

        return False

    direction = get_direction(
        signal
    )

    if direction in (
        "BUY",
        "LONG",
    ):

        return price >= tp2

    if direction in (
        "SELL",
        "SHORT",
    ):

        return price <= tp2

    return False


# =========================================================
# PRICE HIT SL
# =========================================================

def sl_hit(
    signal,
    price: float,
) -> bool:

    sl = get_sl(
        signal
    )

    if sl is None:

        return False

    direction = get_direction(
        signal
    )

    if direction in (
        "BUY",
        "LONG",
    ):

        return price <= sl

    if direction in (
        "SELL",
        "SHORT",
    ):

        return price >= sl

    return False


# =========================================================
# SEND TO CHANNEL
# =========================================================

async def send_channel(
    bot,
    text: str,
    channel_id,
):

    if bot is None:

        logger.error(
            "Bot Telegram tidak tersedia."
        )

        return False

    if not channel_id:

        logger.error(
            "CHANNEL_ID belum tersedia."
        )

        return False

    try:

        await bot.send_message(
            chat_id=channel_id,
            text=text,
            disable_web_page_preview=True,
        )

        return True

    except Exception:

        logger.exception(
            "Gagal mengirim monitoring Telegram."
        )

        return False


# =========================================================
# ENTRY MESSAGE
# =========================================================

def build_entry_message(
    item: MonitorItem,
    price: float,
) -> str:

    direction = get_direction(
        item.signal
    )

    entry = get_entry(
        item.signal
    )

    return (
        "🟢 ENTRY TERSENTUH\n"
        f"{direction} {entry}\n"
        f"Market: {price}\n\n"
        "🎯 Selanjutnya pantau TP1 / SL."
    )


# =========================================================
# TP1 MESSAGE
# =========================================================

def build_tp1_message(
    item: MonitorItem,
) -> str:

    tp1 = get_tp1(
        item.signal
    )

    return (
        "✅ TP1 SUDAH KENA\n"
        f"Profit: 70 pips\n"
        f"TP1: {tp1}\n\n"
        "Jika yakin TP2 masih berpotensi tercapai,\n"
        "silakan lanjutkan dan jangan lupa SL + BE."
    )


# =========================================================
# SL MESSAGE
# =========================================================

def build_sl_message(
    item: MonitorItem,
) -> str:

    sl = get_sl(
        item.signal
    )

    return (
        "❌ SL SUDAH KENA\n"
        f"SL: {sl}\n"
        "Signal selesai."
    )


# =========================================================
# CANCEL MESSAGE
# =========================================================

def build_cancel_message(
    item: MonitorItem,
) -> str:

    entry = get_entry(
        item.signal
    )

    return (
        "⏳ SIGNAL CANCEL\n"
        f"Entry {entry} belum tersentuh "
        "dalam 20 menit.\n"
        "Signal berikutnya akan dilanjutkan."
    )


# =========================================================
# MINUTE 59 MESSAGE
# =========================================================

def build_close_message(
    item: MonitorItem,
) -> str:

    signal_time = get_signal_time(
        item.signal
    )

    return (
        f"⏳ Monitoring signal "
        f"{signal_time.strftime('%H:%M')} diakhiri.\n"
        "1 menit lagi signal baru akan keluar.\n"
        "Semoga entry kita segera menyentuh TP."
    )


# =========================================================
# ADD MONITOR
# =========================================================

async def add_monitor(
    signal,
):

    monitor_id = build_monitor_id(
        signal
    )

    async with _monitor_lock:

        if monitor_id in _active_monitors:

            logger.warning(
                "Signal sudah dimonitor: %s",
                monitor_id,
            )

            return _active_monitors[
                monitor_id
            ]

        # -------------------------------------------------
        # SIMPAN PORTFOLIO
        # -------------------------------------------------

        portfolio_item = None

        try:

            portfolio_item = add_signal(
                signal
            )

        except Exception:

            logger.exception(
                "Gagal menambahkan signal ke portfolio."
            )

        portfolio_id = None

        if portfolio_item:

            portfolio_id = (
                portfolio_item.get(
                    "id"
                )
            )

        # -------------------------------------------------
        # CREATE MONITOR
        # -------------------------------------------------

        item = MonitorItem(

            monitor_id=
                monitor_id,

            signal=
                signal,

            signal_time=
                get_signal_time(
                    signal
                ),

            portfolio_id=
                portfolio_id,
        )

        _active_monitors[
            monitor_id
        ] = item

        logger.info(
            "MONITOR ADDED | %s | %s | entry=%s",
            monitor_id,
            get_direction(signal),
            get_entry(signal),
        )

        return item


# =========================================================
# REMOVE MONITOR
# =========================================================

async def remove_monitor(
    monitor_id: str,
):

    async with _monitor_lock:

        if monitor_id in _active_monitors:

            del _active_monitors[
                monitor_id
            ]

            logger.info(
                "MONITOR REMOVED | %s",
                monitor_id,
            )


# =========================================================
# HANDLE PRICE
# =========================================================

async def process_price(
    item: MonitorItem,
    price: float,
    bot,
    channel_id,
):

    # =====================================================
    # FINISHED
    # =====================================================

    if item.monitoring_finished:

        return


    # =====================================================
    # ENTRY BELUM KENA
    # =====================================================

    if not item.entry_hit:

        if entry_hit(
            item.signal,
            price,
        ):

            item.entry_hit = True

            # ---------------------------------------------
            # PORTFOLIO
            # ---------------------------------------------

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "ENTRY",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update portfolio ENTRY."
                    )

            # ---------------------------------------------
            # TELEGRAM
            # ---------------------------------------------

            await send_channel(
                bot,
                build_entry_message(
                    item,
                    price,
                ),
                channel_id,
            )

            logger.info(
                "ENTRY HIT | %s | price=%s",
                item.monitor_id,
                price,
            )

            return


        # -------------------------------------------------
        # ENTRY TIMEOUT
        # -------------------------------------------------

        age_seconds = (
            now_wib()
            - item.signal_time
        ).total_seconds()

        if age_seconds >= (
            ENTRY_TIMEOUT_MINUTES
            * 60
        ):

            item.cancelled = True

            item.monitoring_finished = True

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "CANCEL",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update portfolio CANCEL."
                    )

            await send_channel(
                bot,
                build_cancel_message(
                    item
                ),
                channel_id,
            )

            logger.info(
                "ENTRY TIMEOUT / CANCEL | %s",
                item.monitor_id,
            )

            return

        return


    # =====================================================
    # TP1 SUDAH KENA
    # =====================================================

    if not item.tp1_hit:

        if tp1_hit(
            item.signal,
            price,
        ):

            item.tp1_hit = True

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "TP1",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update portfolio TP1."
                    )

            await send_channel(
                bot,
                build_tp1_message(
                    item
                ),
                channel_id,
            )

            logger.info(
                "TP1 HIT | %s | price=%s",
                item.monitor_id,
                price,
            )


    # =====================================================
    # TP2
    #
    # TIDAK DIKIRIM KE CHANNEL
    #
    # HANYA PORTFOLIO
    # =====================================================

    if not item.tp2_hit:

        if tp2_hit(
            item.signal,
            price,
        ):

            item.tp2_hit = True

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "TP2",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update portfolio TP2."
                    )

            logger.info(
                "TP2 HIT SILENT | %s | price=%s",
                item.monitor_id,
                price,
            )


    # =====================================================
    # SL
    # =====================================================

    if not item.sl_hit:

        if sl_hit(
            item.signal,
            price,
        ):

            item.sl_hit = True

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "SL",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update portfolio SL."
                    )

            await send_channel(
                bot,
                build_sl_message(
                    item
                ),
                channel_id,
            )

            logger.info(
                "SL HIT | %s | price=%s",
                item.monitor_id,
                price,
            )

            item.monitoring_finished = True


# =========================================================
# CHECK MINUTE 59
# =========================================================

async def check_minute_59(
    item: MonitorItem,
    bot,
    channel_id,
):

    if item.monitoring_finished:

        return

    now = now_wib()

    # -----------------------------------------------------
    # Hanya pada menit 59
    # -----------------------------------------------------

    if now.minute != 59:

        return

    # -----------------------------------------------------
    # Sudah ada TP1 atau SL
    # -----------------------------------------------------

    if item.tp1_hit:

        item.monitoring_finished = True

        return

    if item.sl_hit:

        item.monitoring_finished = True

        return

    # -----------------------------------------------------
    # ENTRY BELUM KENA
    #
    # Kalau sudah lebih dari 20 menit,
    # seharusnya sudah CANCEL.
    # -----------------------------------------------------

    if not item.entry_hit:

        age_seconds = (
            now
            - item.signal_time
        ).total_seconds()

        if age_seconds >= (
            ENTRY_TIMEOUT_MINUTES
            * 60
        ):

            item.cancelled = True

            item.monitoring_finished = True

            if item.portfolio_id:

                try:

                    update_signal(
                        item.portfolio_id,
                        "CANCEL",
                    )

                except Exception:

                    logger.exception(
                        "Gagal update CANCEL minute 59."
                    )

            await send_channel(
                bot,
                build_cancel_message(
                    item
                ),
                channel_id,
            )

        return

    # -----------------------------------------------------
    # ENTRY SUDAH KENA
    #
    # TP1 / SL belum kena
    # -----------------------------------------------------

    await send_channel(
        bot,
        build_close_message(
            item
        ),
        channel_id,
    )

    item.monitoring_finished = True

    logger.info(
        "MONITORING CLOSED :59 | %s",
        item.monitor_id,
    )


# =========================================================
# SCAN ONE SIGNAL
# =========================================================

async def scan_monitor(
    item: MonitorItem,
    bot,
    channel_id,
):

    if item.monitoring_finished:

        return

    # =====================================================
    # HARGA
    # =====================================================

    try:

        price = await asyncio.to_thread(
            get_price
        )

    except Exception:

        logger.exception(
            "Gagal mengambil harga."
        )

        return

    if price is None:

        logger.warning(
            "Harga realtime kosong."
        )

        return

    # =====================================================
    # LAST SCAN
    # =====================================================

    item.last_scan = now_wib()

    logger.info(
        "MONITOR SCAN | "
        "%s | price=%s | entry=%s | tp1=%s | sl=%s",
        item.monitor_id,
        price,
        get_entry(item.signal),
        get_tp1(item.signal),
        get_sl(item.signal),
    )

    # =====================================================
    # PROCESS PRICE
    # =====================================================

    await process_price(
        item,
        price,
        bot,
        channel_id,
    )

    # =====================================================
    # MINUTE 59
    # =====================================================

    await check_minute_59(
        item,
        bot,
        channel_id,
    )


# =========================================================
# SCAN ALL
# =========================================================

async def scan_all(
    bot,
    channel_id,
):

    async with _monitor_lock:

        monitors = list(
            _active_monitors.values()
        )

    if not monitors:

        return

    logger.info(
        "Monitoring %s signal aktif.",
        len(monitors),
    )

    for item in monitors:

        try:

            await scan_monitor(
                item,
                bot,
                channel_id,
            )

        except Exception:

            logger.exception(
                "MONITOR ERROR | %s",
                item.monitor_id,
            )

    # =====================================================
    # CLEAN FINISHED
    # =====================================================

    async with _monitor_lock:

        finished_ids = [

            monitor_id

            for monitor_id, item

            in _active_monitors.items()

            if item.monitoring_finished

        ]

        for monitor_id in finished_ids:

            del _active_monitors[
                monitor_id
            ]

            logger.info(
                "Monitor selesai dihapus | %s",
                monitor_id,
            )


# =========================================================
# MONITOR LOOP
# =========================================================

async def monitor_loop(
    bot,
    channel_id,
):

    logger.info(
        "=========================================="
    )

    logger.info(
        "XAU AI MONITOR ACTIVE"
    )

    logger.info(
        "ENTRY timeout : %s menit",
        ENTRY_TIMEOUT_MINUTES,
    )

    logger.info(
        "Scan interval : %s menit",
        MONITOR_INTERVAL_SECONDS // 60,
    )

    logger.info(
        "TP2           : PORTFOLIO ONLY"
    )

    logger.info(
        "TP1 / SL      : TELEGRAM"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            await scan_all(
                bot,
                channel_id,
            )

        except asyncio.CancelledError:

            logger.info(
                "Monitor dihentikan."
            )

            raise

        except Exception:

            logger.exception(
                "ERROR DI MONITOR LOOP"
            )

        # =================================================
        # WAIT
        # =================================================

        await asyncio.sleep(
            MONITOR_INTERVAL_SECONDS
        )


# =========================================================
# GET ACTIVE MONITORS
# =========================================================

def get_active_monitors():

    return list(
        _active_monitors.values()
    )


# =========================================================
# COUNT ACTIVE
# =========================================================

def count_active_monitors():

    return len(
        _active_monitors
    )
