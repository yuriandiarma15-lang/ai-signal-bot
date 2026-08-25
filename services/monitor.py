"""
services/monitor.py

XAU AI SIGNAL MONITOR
=====================

Fungsi:

1. Menunggu ENTRY tersentuh
2. Scan setiap 10 menit
3. Jika ENTRY tidak tersentuh <= 20 menit:
      -> CANCEL
4. Jika ENTRY tersentuh:
      -> mulai monitoring TP1 + SL
5. TP1:
      -> kirim notifikasi Telegram
      -> simpan hasil portfolio
6. TP2:
      -> TIDAK dikirim ke member
      -> hanya dicatat untuk portfolio
7. SL:
      -> kirim notifikasi Telegram
      -> simpan hasil portfolio
8. Menit :59:
      -> hentikan monitoring signal
      -> kirim pesan penutupan jika TP1/SL belum kena

CANCEL tidak dihitung sebagai LOSS.
"""

import asyncio
import logging

from datetime import datetime
from typing import Any, Dict, Optional

from config.settings import TIMEZONE

from services.twelvedata_client import get_price
from services.sender import send_signal_to_members


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

SCAN_INTERVAL_SECONDS = 10 * 60

ENTRY_TIMEOUT_MINUTES = 20

# Menit 59:
# monitoring signal jam tersebut dihentikan.
STOP_MONITOR_MINUTE = 59


# =========================================================
# MONITOR STATE
# =========================================================

WAITING_ENTRY = "WAITING_ENTRY"

ACTIVE = "ACTIVE"

TP1_HIT = "TP1_HIT"

SL_HIT = "SL_HIT"

TP2_HIT = "TP2_HIT"

CANCELLED = "CANCELLED"

EXPIRED = "EXPIRED"


# =========================================================
# ACTIVE MONITORS
# =========================================================

_monitors: Dict[str, Dict[str, Any]] = {}


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
# SIGNAL ID
# =========================================================

def make_signal_id(
    signal,
) -> str:

    """
    Membuat ID unik berdasarkan:

    tanggal
    jam
    entry
    direction
    """

    timestamp = getattr(
        signal,
        "timestamp",
        None,
    )

    if timestamp is None:

        timestamp = now_wib()

    elif timestamp.tzinfo is None:

        timestamp = timestamp.replace(
            tzinfo=WIB
        )

    else:

        timestamp = timestamp.astimezone(
            WIB
        )

    direction = str(
        getattr(
            signal,
            "bias",
            "UNKNOWN",
        )
    ).upper()

    entry = getattr(
        signal,
        "entry_price",
        0,
    )

    return (
        f"{timestamp.strftime('%Y%m%d_%H%M')}_"
        f"{direction}_"
        f"{entry}"
    )


# =========================================================
# PRICE
# =========================================================

def _price(
    signal,
    field: str,
) -> Optional[float]:

    value = getattr(
        signal,
        field,
        None,
    )

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
# CHECK ENTRY HIT
# =========================================================

def entry_touched(
    direction: str,
    entry: float,
    current_price: float,
) -> bool:

    """
    Entry dianggap tersentuh ketika harga
    mencapai level entry.

    BUY:
        harga <= entry

    SELL:
        harga >= entry
    """

    direction = direction.upper()

    if direction == "BUY":

        return current_price <= entry

    if direction == "SELL":

        return current_price >= entry

    return False


# =========================================================
# CHECK TP1
# =========================================================

def tp1_touched(
    direction: str,
    tp1: float,
    current_price: float,
) -> bool:

    direction = direction.upper()

    if direction == "BUY":

        return current_price >= tp1

    if direction == "SELL":

        return current_price <= tp1

    return False


# =========================================================
# CHECK TP2
# =========================================================

def tp2_touched(
    direction: str,
    tp2: float,
    current_price: float,
) -> bool:

    direction = direction.upper()

    if direction == "BUY":

        return current_price >= tp2

    if direction == "SELL":

        return current_price <= tp2

    return False


# =========================================================
# CHECK SL
# =========================================================

def sl_touched(
    direction: str,
    sl: float,
    current_price: float,
) -> bool:

    direction = direction.upper()

    if direction == "BUY":

        return current_price <= sl

    if direction == "SELL":

        return current_price >= sl

    return False


# =========================================================
# SEND TO MEMBER
# =========================================================

async def _broadcast(
    bot,
    text: str,
):

    """
    Kirim notifikasi ke seluruh member aktif.
    """

    try:

        result = await send_signal_to_members(
            bot,
            text,
        )

        logger.info(
            "Monitor notification sent | result=%s",
            result,
        )

        return result

    except Exception:

        logger.exception(
            "Gagal mengirim monitor notification"
        )

        return None


# =========================================================
# FORMAT ENTRY HIT
# =========================================================

def format_entry_hit(
    monitor,
    price,
) -> str:

    direction = monitor[
        "direction"
    ]

    entry = monitor[
        "entry"
    ]

    return (
        "🟢 ENTRY HIT\n"
        f"{direction} XAUUSD\n"
        f"Entry : {entry}\n"
        f"Price : {price}\n\n"
        "Monitoring TP1 & SL."
    )


# =========================================================
# FORMAT CANCEL
# =========================================================

def format_cancel(
    monitor,
) -> str:

    direction = monitor[
        "direction"
    ]

    entry = monitor[
        "entry"
    ]

    return (
        "⚪ SIGNAL CANCEL\n"
        f"{direction} XAUUSD\n"
        f"Entry : {entry}\n\n"
        "Entry tidak tersentuh dalam 20 menit."
    )


# =========================================================
# FORMAT TP1
# =========================================================

def format_tp1(
    monitor,
) -> str:

    direction = monitor[
        "direction"
    ]

    entry = monitor[
        "entry"
    ]

    tp1 = monitor[
        "tp1"
    ]

    return (
        "✅ TP1 HIT +70 PIPS\n"
        f"{direction} XAUUSD\n"
        f"Entry : {entry}\n"
        f"TP1 : {tp1}\n\n"
        "TP2 masih menjadi target lanjutan.\n"
        "Jika yakin dengan analisa lanjutan, "
        "boleh pertahankan posisi.\n"
        "SL → BE / Profit Lock."
    )


# =========================================================
# FORMAT SL
# =========================================================

def format_sl(
    monitor,
) -> str:

    direction = monitor[
        "direction"
    ]

    entry = monitor[
        "entry"
    ]

    sl = monitor[
        "sl"
    ]

    return (
        "❌ SL HIT\n"
        f"{direction} XAUUSD\n"
        f"Entry : {entry}\n"
        f"SL : {sl}"
    )


# =========================================================
# FORMAT HOUR END
# =========================================================

def format_hour_end(
    monitor,
    hour: int,
) -> str:

    return (
        f"⏳ Monitoring Signal {hour:02d}:00 WIB diakhiri.\n"
        "TP1 / SL belum terkena.\n"
        "1 menit lagi signal baru akan keluar.\n\n"
        "Semoga entry kita segera menyentuh TP."
    )


# =========================================================
# FORMAT TP2 PORTFOLIO
# =========================================================

def format_tp2_portfolio(
    monitor,
) -> str:

    return (
        "TP2 HIT | PORTFOLIO ONLY | "
        f"{monitor['direction']} | "
        f"Entry={monitor['entry']} | "
        f"TP2={monitor['tp2']}"
    )


# =========================================================
# REGISTER SIGNAL
# =========================================================

async def register_signal(
    signal,
    bot,
):

    """
    Daftarkan signal baru ke monitor.

    Signal belum dipantau secara langsung sampai
    monitor worker melakukan scan.
    """

    entry = _price(
        signal,
        "entry_price",
    )

    sl = _price(
        signal,
        "sl",
    )

    tp1 = _price(
        signal,
        "tp1",
    )

    tp2 = _price(
        signal,
        "tp2",
    )

    if None in (
        entry,
        sl,
        tp1,
        tp2,
    ):

        logger.error(
            "Signal monitor invalid | "
            "entry=%s sl=%s tp1=%s tp2=%s",
            entry,
            sl,
            tp1,
            tp2,
        )

        return None

    direction = str(
        getattr(
            signal,
            "bias",
            "",
        )
    ).upper()

    if direction == "BULLISH":

        direction = "BUY"

    elif direction == "BEARISH":

        direction = "SELL"

    if direction not in (
        "BUY",
        "SELL",
    ):

        logger.error(
            "Direction signal tidak valid: %s",
            direction,
        )

        return None

    created_at = now_wib()

    signal_id = make_signal_id(
        signal
    )

    monitor = {

        "id":
            signal_id,

        "signal":
            signal,

        "bot":
            bot,

        "direction":
            direction,

        "entry":
            entry,

        "sl":
            sl,

        "tp1":
            tp1,

        "tp2":
            tp2,

        "created_at":
            created_at,

        "entry_deadline":
            created_at,

        "state":
            WAITING_ENTRY,

        "entry_hit":
            False,

        "tp1_hit":
            False,

        "tp2_hit":
            False,

        "sl_hit":
            False,

        "entry_hit_at":
            None,

        "tp1_hit_at":
            None,

        "tp2_hit_at":
            None,

        "sl_hit_at":
            None,

        "finished":
            False,

    }

    monitor[
        "entry_deadline"
    ] = (
        created_at
    )

    async with _monitor_lock:

        _monitors[
            signal_id
        ] = monitor

    logger.info(
        "MONITOR REGISTERED | "
        "id=%s | "
        "direction=%s | "
        "entry=%s | "
        "tp1=%s | "
        "tp2=%s | "
        "sl=%s",
        signal_id,
        direction,
        entry,
        tp1,
        tp2,
        sl,
    )

    return monitor


# =========================================================
# FINISH MONITOR
# =========================================================

async def _finish(
    signal_id: str,
    state: str,
):

    async with _monitor_lock:

        monitor = _monitors.get(
            signal_id
        )

        if monitor is None:

            return

        monitor[
            "state"
        ] = state

        monitor[
            "finished"
        ] = True

    logger.info(
        "MONITOR FINISHED | id=%s | state=%s",
        signal_id,
        state,
    )


# =========================================================
# PROCESS WAITING ENTRY
# =========================================================

async def _process_waiting_entry(
    monitor,
    current_price,
):

    now = now_wib()

    created_at = monitor[
        "created_at"
    ]

    elapsed_seconds = (
        now - created_at
    ).total_seconds()

    # =====================================================
    # ENTRY HIT
    # =====================================================

    if entry_touched(
        monitor["direction"],
        monitor["entry"],
        current_price,
    ):

        monitor[
            "entry_hit"
        ] = True

        monitor[
            "entry_hit_at"
        ] = now

        monitor[
            "state"
        ] = ACTIVE

        logger.info(
            "ENTRY HIT | "
            "id=%s | "
            "price=%s",
            monitor["id"],
            current_price,
        )

        await _broadcast(
            monitor["bot"],
            format_entry_hit(
                monitor,
                current_price,
            ),
        )

        return

    # =====================================================
    # 20 MINUTE CANCEL
    # =====================================================

    if elapsed_seconds >= (
        ENTRY_TIMEOUT_MINUTES * 60
    ):

        monitor[
            "state"
        ] = CANCELLED

        monitor[
            "finished"
        ] = True

        logger.info(
            "ENTRY CANCEL | "
            "id=%s | "
            "elapsed=%.1f minutes",
            monitor["id"],
            elapsed_seconds / 60,
        )

        await _broadcast(
            monitor["bot"],
            format_cancel(
                monitor
            ),
        )

        return

    # =====================================================
    # NO ACTION
    # =====================================================

    logger.debug(
        "ENTRY belum tersentuh | "
        "id=%s | price=%s | elapsed=%.1f min",
        monitor["id"],
        current_price,
        elapsed_seconds / 60,
    )


# =========================================================
# PROCESS ACTIVE
# =========================================================

async def _process_active(
    monitor,
    current_price,
):

    now = now_wib()

    direction = monitor[
        "direction"
    ]

    # =====================================================
    # TP2
    # =====================================================

    if not monitor[
        "tp2_hit"
    ]:

        if tp2_touched(
            direction,
            monitor["tp2"],
            current_price,
        ):

            monitor[
                "tp2_hit"
            ] = True

            monitor[
                "tp2_hit_at"
            ] = now

            logger.info(
                "TP2 HIT | PORTFOLIO ONLY | "
                "id=%s | price=%s",
                monitor["id"],
                current_price,
            )

            # ---------------------------------------------
            # PENTING:
            # TIDAK broadcast ke member.
            # ---------------------------------------------

            logger.info(
                "%s",
                format_tp2_portfolio(
                    monitor
                ),
            )

    # =====================================================
    # TP1
    # =====================================================

    if not monitor[
        "tp1_hit"
    ]:

        if tp1_touched(
            direction,
            monitor["tp1"],
            current_price,
        ):

            monitor[
                "tp1_hit"
            ] = True

            monitor[
                "tp1_hit_at"
            ] = now

            monitor[
                "state"
            ] = TP1_HIT

            logger.info(
                "TP1 HIT | "
                "id=%s | price=%s",
                monitor["id"],
                current_price,
            )

            await _broadcast(
                monitor["bot"],
                format_tp1(
                    monitor
                ),
            )

    # =====================================================
    # SL
    # =====================================================

    if not monitor[
        "sl_hit"
    ]:

        if sl_touched(
            direction,
            monitor["sl"],
            current_price,
        ):

            monitor[
                "sl_hit"
            ] = True

            monitor[
                "sl_hit_at"
            ] = now

            monitor[
                "state"
            ] = SL_HIT

            monitor[
                "finished"
            ] = True

            logger.info(
                "SL HIT | "
                "id=%s | price=%s",
                monitor["id"],
                current_price,
            )

            await _broadcast(
                monitor["bot"],
                format_sl(
                    monitor
                ),
            )


# =========================================================
# HOUR 59 CHECK
# =========================================================

async def _check_hour_end(
    monitor,
):

    now = now_wib()

    if now.minute != STOP_MONITOR_MINUTE:

        return False

    # =====================================================
    # JIKA SUDAH SELESAI
    # =====================================================

    if monitor[
        "finished"
    ]:

        return True

    # =====================================================
    # ENTRY BELUM KENA
    # =====================================================

    if not monitor[
        "entry_hit"
    ]:

        monitor[
            "finished"
        ] = True

        monitor[
            "state"
        ] = EXPIRED

        logger.info(
            "Signal %s selesai pada :59 "
            "tanpa entry.",
            monitor["id"],
        )

        return True

    # =====================================================
    # ENTRY KENA TAPI TP1 / SL BELUM KENA
    # =====================================================

    if (
        monitor["entry_hit"]
        and
        not monitor["tp1_hit"]
        and
        not monitor["sl_hit"]
    ):

        await _broadcast(
            monitor["bot"],
            format_hour_end(
                monitor,
                now.hour,
            ),
        )

        monitor[
            "finished"
        ] = True

        monitor[
            "state"
        ] = EXPIRED

        logger.info(
            "Monitoring signal %s "
            "dihentikan pada %02d:59 WIB.",
            monitor["id"],
            now.hour,
        )

        return True

    return True


# =========================================================
# PROCESS ONE MONITOR
# =========================================================

async def process_monitor(
    monitor,
):

    if monitor[
        "finished"
    ]:

        return

    # =====================================================
    # HOUR END
    # =====================================================

    ended = await _check_hour_end(
        monitor
    )

    if ended:

        return

    # =====================================================
    # CURRENT PRICE
    # =====================================================

    try:

        current_price = await asyncio.to_thread(
            get_price
        )

    except Exception:

        logger.exception(
            "Gagal mengambil realtime price."
        )

        return

    if current_price is None:

        logger.warning(
            "Realtime price tidak tersedia."
        )

        return

    # =====================================================
    # WAITING ENTRY
    # =====================================================

    if monitor[
        "state"
    ] == WAITING_ENTRY:

        await _process_waiting_entry(
            monitor,
            current_price,
        )

        return

    # =====================================================
    # ACTIVE
    # =====================================================

    if monitor[
        "state"
    ] in (
        ACTIVE,
        TP1_HIT,
    ):

        await _process_active(
            monitor,
            current_price,
        )

        return


# =========================================================
# MONITOR WORKER
# =========================================================

async def monitor_worker():

    """
    Worker utama.

    Setiap 10 menit:

        - ambil harga
        - scan seluruh signal aktif
        - cek entry
        - cek TP1
        - cek SL
        - cek TP2 portfolio

    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "🔎 XAU AI MONITOR WORKER ACTIVE"
    )

    logger.info(
        "Scan interval : 10 menit"
    )

    logger.info(
        "Entry timeout : 20 menit"
    )

    logger.info(
        "TP1           : Telegram"
    )

    logger.info(
        "SL            : Telegram"
    )

    logger.info(
        "TP2           : Portfolio only"
    )

    logger.info(
        "Minute :59     : Stop monitoring"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            # =================================================
            # SNAPSHOT
            # =================================================

            async with _monitor_lock:

                monitors = list(
                    _monitors.values()
                )

            # =================================================
            # CLEAN FINISHED
            # =================================================

            for monitor in monitors:

                if monitor[
                    "finished"
                ]:

                    continue

                try:

                    await process_monitor(
                        monitor
                    )

                except Exception:

                    logger.exception(
                        "Monitor error | id=%s",
                        monitor.get(
                            "id"
                        ),
                    )

            # =================================================
            # REMOVE FINISHED
            # =================================================

            async with _monitor_lock:

                finished_ids = [

                    signal_id

                    for signal_id, monitor
                    in _monitors.items()

                    if monitor.get(
                        "finished",
                        False,
                    )

                ]

                for signal_id in finished_ids:

                    del _monitors[
                        signal_id
                    ]

            # =================================================
            # WAIT
            # =================================================

            await asyncio.sleep(
                SCAN_INTERVAL_SECONDS
            )

        except asyncio.CancelledError:

            logger.info(
                "Monitor worker dihentikan."
            )

            raise

        except Exception:

            logger.exception(
                "ERROR MONITOR WORKER"
            )

            await asyncio.sleep(
                10
            )


# =========================================================
# GET ACTIVE MONITORS
# =========================================================

def get_active_monitors():

    return [

        monitor

        for monitor
        in _monitors.values()

        if not monitor.get(
            "finished",
            False,
        )

    ]


# =========================================================
# GET MONITOR
# =========================================================

def get_monitor(
    signal_id: str,
):

    return _monitors.get(
        signal_id
    )


# =========================================================
# REMOVE MONITOR
# =========================================================

async def remove_monitor(
    signal_id: str,
):

    async with _monitor_lock:

        monitor = _monitors.pop(
            signal_id,
            None,
        )

    if monitor:

        logger.info(
            "Monitor removed | id=%s",
            signal_id,
        )

    return monitor


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "XAU AI SIGNAL MONITOR"
    )

    print(
        "Scan : 10 minutes"
    )

    print(
        "Entry timeout : 20 minutes"
    )

    print(
        "TP1 / SL : Telegram"
    )

    print(
        "TP2 : Portfolio only"
    )
