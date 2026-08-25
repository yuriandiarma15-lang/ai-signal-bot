"""
XAU AI SIGNAL MONITOR

FUNGSI:

1. Monitor ENTRY pending
2. ENTRY tidak tersentuh maksimal 20 menit -> CANCEL
3. ENTRY tersentuh -> ENTRY HIT
4. Setelah ENTRY HIT:
      monitor TP1 dan SL
5. TP1 kena -> broadcast TP1
6. SL kena -> broadcast SL
7. TP2 tidak dibroadcast
      hanya dicatat untuk performance
8. Menit 59:
      public monitoring dihentikan
9. Scan setiap 10 menit
10. Menggunakan candle M1 agar tidak melewatkan
    harga yang sempat menyentuh level.

STATUS:

WAITING_ENTRY
ACTIVE
TP1
SL
TP2
CANCELLED
MONITORING_ENDED
"""

import asyncio
import json
import logging
import os

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from config.settings import TIMEZONE

from services.twelvedata_client import get_candles


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
# FILE
# =========================================================

DATA_DIR = "data"

TRACKING_FILE = os.path.join(
    DATA_DIR,
    "signal_tracking.json",
)


# =========================================================
# SETTINGS
# =========================================================

SCAN_INTERVAL_MINUTES = 10

ENTRY_TIMEOUT_MINUTES = 20

PUBLIC_MONITOR_END_MINUTE = 59

M1_LOOKBACK_MINUTES = 12


# =========================================================
# MONITOR LOCK
# =========================================================

_monitor_running = False


# =========================================================
# JSON LOAD
# =========================================================

def _load_tracking() -> List[Dict[str, Any]]:

    if not os.path.exists(
        TRACKING_FILE
    ):

        return []

    try:

        with open(
            TRACKING_FILE,
            "r",
            encoding="utf-8",
        ) as f:

            data = json.load(
                f
            )

        if not isinstance(
            data,
            list,
        ):

            return []

        return data

    except Exception:

        logger.exception(
            "Gagal membaca %s",
            TRACKING_FILE,
        )

        return []


# =========================================================
# JSON SAVE
# =========================================================

def _save_tracking(
    data: List[Dict[str, Any]],
):

    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    temp_file = (
        TRACKING_FILE
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
            TRACKING_FILE,
        )

    except Exception:

        logger.exception(
            "Gagal menyimpan tracking signal"
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
# TIME
# =========================================================

def _now() -> datetime:

    return datetime.now(
        WIB
    )


# =========================================================
# DATETIME PARSER
# =========================================================

def _parse_datetime(
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

        except Exception:

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
# PRICE
# =========================================================

def _price(
    value
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
# SIGNAL ID
# =========================================================

def _make_signal_id(
    signal,
    created_at: datetime,
) -> str:

    entry = _price(
        getattr(
            signal,
            "entry_price",
            None,
        )
    )

    direction = str(
        getattr(
            signal,
            "bias",
            "",
        )
    ).upper()

    return (
        f"{created_at.strftime('%Y%m%d_%H%M%S')}"
        f"_{direction}"
        f"_{entry}"
    )


# =========================================================
# REGISTER SIGNAL
# =========================================================

def register_signal(
    signal,
) -> Optional[str]:
    """
    Mendaftarkan signal baru ke monitoring.
    """

    try:

        now = _now()

        direction = str(
            getattr(
                signal,
                "bias",
                "",
            )
        ).lower().strip()

        if direction in (
            "bullish",
            "buy",
        ):

            direction = "BUY"

        elif direction in (
            "bearish",
            "sell",
        ):

            direction = "SELL"

        else:

            logger.error(
                "Direction signal tidak valid: %s",
                direction,
            )

            return None

        entry = _price(
            getattr(
                signal,
                "entry_price",
                None,
            )
        )

        tp1 = _price(
            getattr(
                signal,
                "tp1",
                None,
            )
        )

        tp2 = _price(
            getattr(
                signal,
                "tp2",
                None,
            )
        )

        sl = _price(
            getattr(
                signal,
                "sl",
                None,
            )
        )

        if not all([
            entry is not None,
            tp1 is not None,
            tp2 is not None,
            sl is not None,
        ]):

            logger.error(
                "Signal tidak memiliki harga lengkap."
            )

            return None

        data = _load_tracking()

        signal_id = _make_signal_id(
            signal,
            now,
        )

        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        for item in data:

            if item.get(
                "signal_id"
            ) == signal_id:

                logger.warning(
                    "Signal sudah terdaftar: %s",
                    signal_id,
                )

                return signal_id

        # -------------------------------------------------
        # SIGNAL
        # -------------------------------------------------

        item = {

            "signal_id":
                signal_id,

            "signal_time":
                now.isoformat(),

            "direction":
                direction,

            "entry_price":
                entry,

            "tp1_price":
                tp1,

            "tp2_price":
                tp2,

            "sl_price":
                sl,

            # ---------------------------------------------
            # STATUS
            # ---------------------------------------------

            "status":
                "WAITING_ENTRY",

            "public_monitoring":
                True,

            # ---------------------------------------------
            # ENTRY
            # ---------------------------------------------

            "entry_hit":
                False,

            "entry_hit_at":
                None,

            # ---------------------------------------------
            # TP1
            # ---------------------------------------------

            "tp1_hit":
                False,

            "tp1_hit_at":
                None,

            # ---------------------------------------------
            # TP2
            # ---------------------------------------------

            "tp2_hit":
                False,

            "tp2_hit_at":
                None,

            # ---------------------------------------------
            # SL
            # ---------------------------------------------

            "sl_hit":
                False,

            "sl_hit_at":
                None,

            # ---------------------------------------------
            # CANCEL
            # ---------------------------------------------

            "cancelled_at":
                None,

            # ---------------------------------------------
            # PUBLIC END
            # ---------------------------------------------

            "monitoring_ended_at":
                None,

            # ---------------------------------------------
            # LAST SCAN
            # ---------------------------------------------

            "last_scan_at":
                None,

        }

        data.append(
            item
        )

        _save_tracking(
            data
        )

        logger.info(
            "📡 SIGNAL REGISTERED | "
            "%s | %s | ENTRY=%s | TP1=%s | TP2=%s | SL=%s",
            signal_id,
            direction,
            entry,
            tp1,
            tp2,
            sl,
        )

        return signal_id

    except Exception:

        logger.exception(
            "REGISTER SIGNAL ERROR"
        )

        return None


# =========================================================
# CHECK LEVEL
# =========================================================

def _entry_hit(
    direction: str,
    candle: Dict[str, Any],
    entry: float,
) -> bool:

    high = _price(
        candle.get(
            "high"
        )
    )

    low = _price(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    if direction == "BUY":

        return low <= entry

    return high >= entry


def _tp1_hit(
    direction: str,
    candle: Dict[str, Any],
    tp1: float,
) -> bool:

    high = _price(
        candle.get(
            "high"
        )
    )

    low = _price(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    if direction == "BUY":

        return high >= tp1

    return low <= tp1


def _tp2_hit(
    direction: str,
    candle: Dict[str, Any],
    tp2: float,
) -> bool:

    high = _price(
        candle.get(
            "high"
        )
    )

    low = _price(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    if direction == "BUY":

        return high >= tp2

    return low <= tp2


def _sl_hit(
    direction: str,
    candle: Dict[str, Any],
    sl: float,
) -> bool:

    high = _price(
        candle.get(
            "high"
        )
    )

    low = _price(
        candle.get(
            "low"
        )
    )

    if high is None or low is None:

        return False

    if direction == "BUY":

        return low <= sl

    return high >= sl


# =========================================================
# GET M1 CANDLES
# =========================================================

def _get_recent_candles():

    try:

        candles = get_candles(
            interval="1min",
            outputsize=M1_LOOKBACK_MINUTES,
        )

        if not candles:

            logger.warning(
                "Tidak ada candle M1."
            )

            return []

        return candles

    except Exception:

        logger.exception(
            "Gagal mengambil candle M1."
        )

        return []


# =========================================================
# SEND MESSAGE
# =========================================================

async def _send(
    bot,
    text: str,
):

    """
    Mengirim pesan ke seluruh member.

    Untuk sementara menggunakan sender
    yang sama dengan signal utama.
    """

    try:

        from services.sender import (
            send_message_to_members,
        )

        result = await send_message_to_members(
            bot,
            text,
        )

        return result

    except ImportError:

        logger.warning(
            "send_message_to_members belum tersedia."
        )

        return False

    except Exception:

        logger.exception(
            "Gagal mengirim monitor message."
        )

        return False


# =========================================================
# ENTRY HIT MESSAGE
# =========================================================

def _entry_message(
    item
) -> str:

    direction = item[
        "direction"
    ]

    entry = item[
        "entry_price"
    ]

    return (
        "🟢 ENTRY HIT\n"
        f"{direction} XAUUSD @ {entry}"
    )


# =========================================================
# TP1 MESSAGE
# =========================================================

def _tp1_message(
    item
) -> str:

    return (
        "✅ TP1 HIT\n"
        "+70 PIPS\n\n"
        "TP2 masih terbuka.\n"
        "Jika ingin lanjut, gunakan BE / SL+.\n\n"
        "⚠️ TP2 menjadi tanggung jawab masing-masing."
    )


# =========================================================
# SL MESSAGE
# =========================================================

def _sl_message(
    item
) -> str:

    return (
        "❌ SL HIT\n"
        "Signal selesai."
    )


# =========================================================
# CANCEL MESSAGE
# =========================================================

def _cancel_message(
    item
) -> str:

    signal_time = _parse_datetime(
        item.get(
            "signal_time"
        )
    )

    if signal_time:

        time_text = signal_time.strftime(
            "%H:%M"
        )

    else:

        time_text = "-"

    return (
        "❌ SIGNAL "
        f"{time_text} CANCEL\n"
        "Entry tidak tersentuh dalam 20 menit."
    )


# =========================================================
# END MONITOR MESSAGE
# =========================================================

def _monitoring_end_message(
    item
) -> str:

    signal_time = _parse_datetime(
        item.get(
            "signal_time"
        )
    )

    if signal_time:

        time_text = signal_time.strftime(
            "%H:%M"
        )

    else:

        time_text = "-"

    return (
        f"⏳ MONITORING SIGNAL {time_text} DIAKHIRI\n\n"
        "TP1 / SL belum tersentuh.\n"
        "1 menit lagi signal baru akan keluar.\n\n"
        "Semoga entry kita segera menyentuh TP."
    )


# =========================================================
# MONITOR ENTRY
# =========================================================

async def _monitor_waiting_entry(
    bot,
    item,
    candles,
    now,
) -> bool:

    signal_time = _parse_datetime(
        item.get(
            "signal_time"
        )
    )

    if signal_time is None:

        return False

    age_seconds = (
        now - signal_time
    ).total_seconds()

    # -----------------------------------------------------
    # 20 MENIT
    # -----------------------------------------------------

    if age_seconds >= (
        ENTRY_TIMEOUT_MINUTES * 60
    ):

        item[
            "status"
        ] = "CANCELLED"

        item[
            "cancelled_at"
        ] = now.isoformat()

        item[
            "public_monitoring"
        ] = False

        logger.info(
            "❌ ENTRY TIMEOUT | %s",
            item.get(
                "signal_id"
            ),
        )

        await _send(
            bot,
            _cancel_message(
                item
            ),
        )

        return True

    # -----------------------------------------------------
    # CHECK ENTRY
    # -----------------------------------------------------

    direction = item[
        "direction"
    ]

    entry = item[
        "entry_price"
    ]

    for candle in candles:

        if _entry_hit(
            direction,
            candle,
            entry,
        ):

            item[
                "entry_hit"
            ] = True

            item[
                "entry_hit_at"
            ] = now.isoformat()

            item[
                "status"
            ] = "ACTIVE"

            logger.info(
                "🟢 ENTRY HIT | %s | %s",
                item.get(
                    "signal_id"
                ),
                entry,
            )

            await _send(
                bot,
                _entry_message(
                    item
                ),
            )

            return True

    return False


# =========================================================
# MONITOR ACTIVE
# =========================================================

async def _monitor_active(
    bot,
    item,
    candles,
    now,
) -> bool:

    direction = item[
        "direction"
    ]

    tp1 = item[
        "tp1_price"
    ]

    tp2 = item[
        "tp2_price"
    ]

    sl = item[
        "sl_price"
    ]

    changed = False

    # =====================================================
    # TP2 INTERNAL
    # =====================================================

    if not item.get(
        "tp2_hit",
        False,
    ):

        for candle in candles:

            if _tp2_hit(
                direction,
                candle,
                tp2,
            ):

                item[
                    "tp2_hit"
                ] = True

                item[
                    "tp2_hit_at"
                ] = now.isoformat()

                logger.info(
                    "🎯 TP2 INTERNAL HIT | %s",
                    item.get(
                        "signal_id"
                    ),
                )

                changed = True

                break

    # =====================================================
    # TP1
    # =====================================================

    if not item.get(
        "tp1_hit",
        False,
    ):

        for candle in candles:

            if _tp1_hit(
                direction,
                candle,
                tp1,
            ):

                item[
                    "tp1_hit"
                ] = True

                item[
                    "tp1_hit_at"
                ] = now.isoformat()

                item[
                    "status"
                ] = "TP1"

                logger.info(
                    "✅ TP1 HIT | %s",
                    item.get(
                        "signal_id"
                    ),
                )

                await _send(
                    bot,
                    _tp1_message(
                        item
                    ),
                )

                changed = True

                break

    # =====================================================
    # SL
    # =====================================================

    if not item.get(
        "sl_hit",
        False,
    ):

        for candle in candles:

            if _sl_hit(
                direction,
                candle,
                sl,
            ):

                item[
                    "sl_hit"
                ] = True

                item[
                    "sl_hit_at"
                ] = now.isoformat()

                item[
                    "status"
                ] = "SL"

                logger.info(
                    "❌ SL HIT | %s",
                    item.get(
                        "signal_id"
                    ),
                )

                await _send(
                    bot,
                    _sl_message(
                        item
                    ),
                )

                item[
                    "public_monitoring"
                ] = False

                changed = True

                break

    return changed


# =========================================================
# MINUTE 59 STOP
# =========================================================

async def _check_public_monitor_end(
    bot,
    item,
    now,
) -> bool:

    if not item.get(
        "public_monitoring",
        True,
    ):

        return False

    # -----------------------------------------------------
    # ONLY MINUTE 59
    # -----------------------------------------------------

    if now.minute != (
        PUBLIC_MONITOR_END_MINUTE
    ):

        return False

    # -----------------------------------------------------
    # FINAL RESULT ALREADY
    # -----------------------------------------------------

    if item.get(
        "status"
    ) in (
        "CANCELLED",
        "SL",
    ):

        return False

    # -----------------------------------------------------
    # END PUBLIC MONITOR
    # -----------------------------------------------------

    item[
        "public_monitoring"
    ] = False

    item[
        "status"
    ] = "MONITORING_ENDED"

    item[
        "monitoring_ended_at"
    ] = now.isoformat()

    logger.info(
        "⏳ PUBLIC MONITORING ENDED | %s",
        item.get(
            "signal_id"
        ),
    )

    await _send(
        bot,
        _monitoring_end_message(
            item
        ),
    )

    return True


# =========================================================
# PROCESS ONE SIGNAL
# =========================================================

async def _process_item(
    bot,
    item,
    candles,
    now,
):

    try:

        # -------------------------------------------------
        # FINAL STATUS
        # -------------------------------------------------

        if item.get(
            "status"
        ) in (
            "CANCELLED",
            "SL",
        ):

            return False

        # -------------------------------------------------
        # PUBLIC END CHECK
        # -------------------------------------------------

        if await _check_public_monitor_end(
            bot,
            item,
            now,
        ):

            return True

        # -------------------------------------------------
        # PUBLIC MONITOR STOPPED
        # -------------------------------------------------

        if not item.get(
            "public_monitoring",
            True,
        ):

            return False

        # -------------------------------------------------
        # WAITING ENTRY
        # -------------------------------------------------

        if item.get(
            "status"
        ) == "WAITING_ENTRY":

            return await _monitor_waiting_entry(
                bot,
                item,
                candles,
                now,
            )

        # -------------------------------------------------
        # ACTIVE / TP1
        # -------------------------------------------------

        if item.get(
            "status"
        ) in (
            "ACTIVE",
            "TP1",
        ):

            return await _monitor_active(
                bot,
                item,
                candles,
                now,
            )

        return False

    except Exception:

        logger.exception(
            "PROCESS MONITOR ITEM ERROR | %s",
            item.get(
                "signal_id"
            ),
        )

        return False


# =========================================================
# SCAN
# =========================================================

async def scan_signals(
    bot,
):

    now = _now()

    data = _load_tracking()

    if not data:

        return

    # =====================================================
    # CANDLES
    # =====================================================

    candles = await asyncio.to_thread(
        _get_recent_candles
    )

    if not candles:

        logger.warning(
            "Scan dibatalkan karena candle M1 kosong."
        )

        return

    changed = False

    # =====================================================
    # PROCESS
    # =====================================================

    for item in data:

        result = await _process_item(
            bot,
            item,
            candles,
            now,
        )

        if result:

            changed = True

        item[
            "last_scan_at"
        ] = now.isoformat()

    # =====================================================
    # SAVE
    # =====================================================

    if changed or data:

        _save_tracking(
            data
        )


# =========================================================
# MONITOR LOOP
# =========================================================

async def monitor_scheduler(
    bot,
):

    global _monitor_running

    if _monitor_running:

        logger.warning(
            "Monitor scheduler sudah berjalan."
        )

        return

    _monitor_running = True

    logger.info(
        "=========================================="
    )

    logger.info(
        "📡 XAU AI SIGNAL MONITOR ACTIVE"
    )

    logger.info(
        "Scan interval : %s menit",
        SCAN_INTERVAL_MINUTES,
    )

    logger.info(
        "Entry timeout : %s menit",
        ENTRY_TIMEOUT_MINUTES,
    )

    logger.info(
        "Public end    : menit %s",
        PUBLIC_MONITOR_END_MINUTE,
    )

    logger.info(
        "TP2           : INTERNAL ONLY"
    )

    logger.info(
        "=========================================="
    )

    try:

        while True:

            try:

                await scan_signals(
                    bot
                )

            except Exception:

                logger.exception(
                    "ERROR MONITOR SCAN"
                )

            # -------------------------------------------------
            # SCAN SETIAP 10 MENIT
            # -------------------------------------------------

            await asyncio.sleep(
                SCAN_INTERVAL_MINUTES * 60
            )

    except asyncio.CancelledError:

        logger.info(
            "Signal monitor dihentikan."
        )

        raise

    finally:

        _monitor_running = False


# =========================================================
# GET TRACKING
# =========================================================

def get_tracking() -> List[Dict[str, Any]]:

    return _load_tracking()


# =========================================================
# GET ACTIVE
# =========================================================

def get_active_tracking() -> List[Dict[str, Any]]:

    data = _load_tracking()

    return [

        item

        for item in data

        if item.get(
            "status"
        ) not in (
            "CANCELLED",
            "SL",
        )

    ]


# =========================================================
# CLEAN OLD TRACKING
# =========================================================

def clean_old_tracking(
    days: int = 7,
):

    data = _load_tracking()

    now = _now()

    cleaned = []

    removed = 0

    for item in data:

        signal_time = _parse_datetime(
            item.get(
                "signal_time"
            )
        )

        if signal_time is None:

            cleaned.append(
                item
            )

            continue

        age = (
            now - signal_time
        ).total_seconds()

        if age > (
            days * 86400
        ):

            removed += 1

            continue

        cleaned.append(
            item
        )

    if removed:

        _save_tracking(
            cleaned
        )

        logger.info(
            "Tracking lama dihapus: %s",
            removed,
        )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "XAU AI SIGNAL MONITOR"
    )

    print(
        "Tracking file:",
        TRACKING_FILE,
    )
