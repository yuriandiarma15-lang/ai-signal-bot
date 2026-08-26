"""
services/scheduler.py

XAU AI SIGNAL SCHEDULER
=======================

JADWAL SIGNAL:

SENIN
07:00 - 23:00

SELASA - JUMAT
00:00 - 02:00
07:00 - 23:00

SABTU
00:00 - 02:00

MINGGU
CLOSED


ALUR:

SCHEDULER
    |
    v
BUILD SIGNAL
    |
    v
TELEGRAM REALTIME
    |
    v
MONITOR
    |
    +--> WAIT ENTRY max 20 menit
    |
    +--> ENTRY HIT
    |       |
    |       +--> TP1
    |       |
    |       +--> SL
    |
    +--> ENTRY tidak kena
            |
            +--> CANCEL


STRATEGY:

M5 Structure
M1 Entry Timing
SMC
Order Block
FVG
Liquidity
BOS / CHoCH
Risk Management


CATATAN:

Website SUDAH TIDAK DIGUNAKAN.

Telegram:
    REALTIME

Monitor:
    Scan setiap 5 menit

Entry:
    Maksimal ditunggu 20 menit

TP1:
    Hasil utama Performance

SL:
    Hasil utama Performance

TP2:
    Tidak dikirim sebagai hasil monitoring publik.
    Menjadi tanggung jawab masing-masing user.
"""

import asyncio
import logging

from datetime import datetime, timedelta

import pytz


from config.settings import (
    TIMEZONE,
)


from services.signal_builder import (
    build_signal,
)


from services.sender import (
    send_signal_to_members,
)


from services.monitor import (
    add_signal,
)


# =========================================================
# TIMEZONE
# =========================================================

WIB = pytz.timezone(
    TIMEZONE
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    "signal_scheduler"
)


# =========================================================
# SIGNAL LOCK
# =========================================================

_signal_running = False


# =========================================================
# LAST SIGNAL TIME
# =========================================================

_last_signal_time = None


# =========================================================
# TRADING OPEN
# =========================================================

def trading_open(
    dt=None,
):
    """
    Jadwal XAU AI Signal.

    SENIN
        07:00 - 23:59

    SELASA - JUMAT
        00:00 - 02:00
        07:00 - 23:59

    SABTU
        00:00 - 02:00

    MINGGU
        CLOSED
    """

    # =====================================================
    # CURRENT TIME
    # =====================================================

    if dt is None:

        now = datetime.now(
            WIB
        )

    else:

        if dt.tzinfo is None:

            now = WIB.localize(
                dt
            )

        else:

            now = dt.astimezone(
                WIB
            )

    weekday = now.weekday()

    current_minutes = (
        now.hour * 60
        + now.minute
    )

    # =====================================================
    # MINGGU
    # =====================================================

    if weekday == 6:

        return False

    # =====================================================
    # SENIN
    # =====================================================

    if weekday == 0:

        return (
            current_minutes >= 7 * 60
        )

    # =====================================================
    # SELASA - JUMAT
    # =====================================================

    if weekday in (
        1,
        2,
        3,
        4,
    ):

        # -----------------------------------------------
        # 00:00 - 02:00
        # -----------------------------------------------

        if current_minutes <= 2 * 60:

            return True

        # -----------------------------------------------
        # 07:00 - 23:59
        # -----------------------------------------------

        if current_minutes >= 7 * 60:

            return True

        return False

    # =====================================================
    # SABTU
    # =====================================================

    if weekday == 5:

        return (
            current_minutes <= 2 * 60
        )

    return False


# =========================================================
# VALID SIGNAL HOURS
# =========================================================

def is_signal_hour(
    dt=None,
):
    """
    Signal hanya dibuat tepat pada jam:

    00
    01
    02

    dan:

    07
    08
    ...
    23
    """

    if dt is None:

        now = datetime.now(
            WIB
        )

    else:

        if dt.tzinfo is None:

            now = WIB.localize(
                dt
            )

        else:

            now = dt.astimezone(
                WIB
            )

    # =====================================================
    # MARKET CHECK
    # =====================================================

    if not trading_open(
        now
    ):

        return False

    hour = now.hour

    # =====================================================
    # JAM 00 - 02
    # =====================================================

    if hour in (
        0,
        1,
        2,
    ):

        return True

    # =====================================================
    # JAM 07 - 23
    # =====================================================

    if 7 <= hour <= 23:

        return True

    return False


# =========================================================
# NEXT SIGNAL TIME
# =========================================================

def next_signal_time():
    """
    Mencari jadwal signal berikutnya.

    Contoh:

    Senin 06:30
        -> Senin 07:00

    Senin 07:30
        -> Senin 08:00

    Jumat 23:30
        -> Sabtu 00:00

    Sabtu 01:30
        -> Sabtu 02:00

    Sabtu 02:30
        -> Senin 07:00

    Minggu
        -> Senin 07:00
    """

    now = datetime.now(
        WIB
    )

    # =====================================================
    # AWAL JAM BERIKUTNYA
    # =====================================================

    target = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    if target <= now:

        target += timedelta(
            hours=1
        )

    # =====================================================
    # CARI JAM VALID
    # =====================================================

    for _ in range(200):

        if is_signal_hour(
            target
        ):

            return target

        target += timedelta(
            hours=1
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    raise RuntimeError(
        "Tidak dapat menemukan "
        "jadwal signal berikutnya."
    )


# =========================================================
# DUPLICATE PROTECTION
# =========================================================

def _already_processed_this_hour(
    dt: datetime,
) -> bool:

    global _last_signal_time

    if _last_signal_time is None:

        return False

    return (
        _last_signal_time.year
        == dt.year

        and

        _last_signal_time.month
        == dt.month

        and

        _last_signal_time.day
        == dt.day

        and

        _last_signal_time.hour
        == dt.hour
    )


# =========================================================
# PROCESS SIGNAL
# =========================================================

async def process_signal(
    bot,
):

    global _signal_running
    global _last_signal_time

    # =====================================================
    # LOCK
    # =====================================================

    if _signal_running:

        logger.warning(
            "Signal sebelumnya masih diproses. "
            "Job dilewati."
        )

        return

    _signal_running = True

    try:

        # =================================================
        # CURRENT TIME
        # =================================================

        now = datetime.now(
            WIB
        )

        # =================================================
        # MARKET CHECK
        # =================================================

        if not trading_open(
            now
        ):

            logger.info(
                "Market CLOSED. "
                "Signal tidak dibuat."
            )

            return

        # =================================================
        # SIGNAL HOUR CHECK
        # =================================================

        if not is_signal_hour(
            now
        ):

            logger.info(
                "Bukan jam signal. "
                "Current hour=%02d",
                now.hour,
            )

            return

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        if _already_processed_this_hour(
            now
        ):

            logger.warning(
                "Signal %02d:00 sudah diproses. "
                "Skip duplicate.",
                now.hour,
            )

            return

        # =================================================
        # HEADER LOG
        # =================================================

        logger.info(
            "=========================================="
        )

        logger.info(
            "GENERATING XAUUSD SMC SIGNAL"
        )

        logger.info(
            "Waktu: %s",
            now.strftime(
                "%d-%m-%Y %H:%M:%S WIB"
            ),
        )

        # =================================================
        # BUILD SIGNAL
        # =================================================

        try:

            signal = await asyncio.to_thread(
                build_signal
            )

        except Exception:

            logger.exception(
                "BUILD SIGNAL ERROR"
            )

            return

        # =================================================
        # VALIDATE SIGNAL
        # =================================================

        if signal is None:

            logger.warning(
                "build_signal() menghasilkan None."
            )

            return

        # =================================================
        # LOG SIGNAL
        # =================================================

        logger.info(
            "SIGNAL CREATED | "
            "bias=%s | "
            "entry=%s | "
            "order=%s | "
            "pending=%s | "
            "probability=%s%% | "
            "zone=%s | "
            "fill=%s",
            getattr(
                signal,
                "bias",
                "-",
            ),
            getattr(
                signal,
                "entry_price",
                "-",
            ),
            getattr(
                signal,
                "order_type",
                "-",
            ),
            getattr(
                signal,
                "is_pending",
                "-",
            ),
            getattr(
                signal,
                "probability",
                "-",
            ),
            getattr(
                signal,
                "zone_type",
                "-",
            ),
            getattr(
                signal,
                "fill_status",
                "-",
            ),
        )

        # =================================================
        # TELEGRAM REALTIME
        # =================================================

        telegram_success = False

        try:

            telegram_result = (
                await send_signal_to_members(
                    bot,
                    signal,
                )
            )

            logger.info(
                "TELEGRAM RESULT: %s",
                telegram_result,
            )

            # ---------------------------------------------
            # RESULT DICT
            # ---------------------------------------------

            if isinstance(
                telegram_result,
                dict,
            ):

                telegram_success = (
                    telegram_result.get(
                        "success",
                        0,
                    ) > 0
                )

            # ---------------------------------------------
            # RESULT BOOLEAN
            # ---------------------------------------------

            else:

                telegram_success = bool(
                    telegram_result
                )

        except Exception:

            logger.exception(
                "Telegram send error"
            )

            telegram_success = False

        # =================================================
        # TELEGRAM GAGAL TOTAL
        # =================================================

        if not telegram_success:

            logger.error(
                "Tidak ada member yang menerima "
                "signal Telegram."
            )

            return

        # =================================================
        # MARK PROCESSED
        # =================================================

        _last_signal_time = now

        # =================================================
        # ADD SIGNAL TO MONITOR
        # =================================================

        try:

            monitor_added = await add_signal(
                signal
            )

            if monitor_added:

                logger.info(
                    "SIGNAL ADDED TO MONITOR | "
                    "Entry timeout=%s menit | "
                    "Monitor scan=5 menit",
                    20,
                )

            else:

                logger.warning(
                    "Signal gagal ditambahkan ke monitor."
                )

        except Exception:

            logger.exception(
                "Gagal menambahkan signal "
                "ke monitor."
            )

        # =================================================
        # COMPLETE
        # =================================================

        logger.info(
            "SIGNAL PROCESS COMPLETE"
        )

        logger.info(
            "Telegram : REALTIME"
        )

        logger.info(
            "Monitor  : ACTIVE"
        )

        logger.info(
            "Scan     : EVERY 5 MINUTES"
        )

        logger.info(
            "Entry    : MAX 20 MINUTES"
        )

        logger.info(
            "TP1      : PERFORMANCE"
        )

        logger.info(
            "SL       : PERFORMANCE"
        )

        logger.info(
            "TP2      : USER RESPONSIBILITY"
        )

        logger.info(
            "Website  : DISABLED"
        )

        logger.info(
            "=========================================="
        )

    finally:

        _signal_running = False


# =========================================================
# SIGNAL SCHEDULER
# =========================================================

async def signal_scheduler(
    bot,
):

    logger.info(
        "=========================================="
    )

    logger.info(
        "⏰ XAU AI SIGNAL SCHEDULER ACTIVE"
    )

    logger.info(
        "Senin       : 07:00 - 23:00 WIB"
    )

    logger.info(
        "Selasa-Jumat: 00:00 - 02:00 + "
        "07:00 - 23:00 WIB"
    )

    logger.info(
        "Sabtu       : 00:00 - 02:00 WIB"
    )

    logger.info(
        "Minggu      : CLOSED"
    )

    logger.info(
        "Telegram    : REALTIME"
    )

    logger.info(
        "Monitor     : EVERY 5 MINUTES"
    )

    logger.info(
        "Entry       : MAX 20 MINUTES"
    )

    logger.info(
        "TP1         : PERFORMANCE"
    )

    logger.info(
        "SL          : PERFORMANCE"
    )

    logger.info(
        "TP2         : USER RESPONSIBILITY"
    )

    logger.info(
        "Website     : DISABLED"
    )

    logger.info(
        "Timeframe   : M5 Structure + M1 Entry"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            # =================================================
            # CURRENT TIME
            # =================================================

            now = datetime.now(
                WIB
            )

            # =================================================
            # NEXT SIGNAL
            # =================================================

            next_run = (
                next_signal_time()
            )

            wait_seconds = (
                next_run - now
            ).total_seconds()

            logger.info(
                "NOW: %s",
                now.strftime(
                    "%d-%m-%Y %H:%M:%S WIB"
                ),
            )

            logger.info(
                "NEXT SIGNAL: %s",
                next_run.strftime(
                    "%d-%m-%Y %H:%M WIB"
                ),
            )

            logger.info(
                "WAIT: %.1f detik",
                max(
                    wait_seconds,
                    0,
                ),
            )

            # =================================================
            # WAIT
            # =================================================

            await asyncio.sleep(
                max(
                    wait_seconds,
                    1,
                )
            )

            # =================================================
            # WAKE UP
            # =================================================

            check_time = datetime.now(
                WIB
            )

            logger.info(
                "Scheduler wake-up: %s",
                check_time.strftime(
                    "%d-%m-%Y %H:%M:%S WIB"
                ),
            )

            # =================================================
            # MINUTE CHECK
            # =================================================

            if check_time.minute != 0:

                logger.warning(
                    "Scheduler bangun bukan "
                    "pada menit 00. "
                    "Current=%s. "
                    "Mencari jadwal berikutnya.",
                    check_time.strftime(
                        "%H:%M:%S"
                    ),
                )

                continue

            # =================================================
            # MARKET CHECK
            # =================================================

            if not trading_open(
                check_time
            ):

                logger.info(
                    "Market CLOSED saat "
                    "scheduler wake-up."
                )

                continue

            # =================================================
            # SIGNAL HOUR CHECK
            # =================================================

            if not is_signal_hour(
                check_time
            ):

                logger.info(
                    "Bukan jam signal."
                )

                continue

            # =================================================
            # PROCESS SIGNAL
            # =================================================

            await process_signal(
                bot
            )

            # =================================================
            # SMALL DELAY
            # =================================================

            await asyncio.sleep(
                2
            )

        # =====================================================
        # CANCEL
        # =====================================================

        except asyncio.CancelledError:

            logger.info(
                "Signal scheduler dihentikan."
            )

            raise

        # =====================================================
        # ERROR
        # =====================================================

        except Exception:

            logger.exception(
                "ERROR DI SIGNAL SCHEDULER"
            )

            await asyncio.sleep(
                10
            )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "=========================================="
    )

    print(
        "XAU AI SIGNAL SCHEDULER TEST"
    )

    print(
        "=========================================="
    )

    now = datetime.now(
        WIB
    )

    print(
        "NOW:",
        now.strftime(
            "%d-%m-%Y %H:%M:%S WIB"
        )
    )

    print(
        "TRADING OPEN:",
        trading_open(
            now
        )
    )

    print(
        "SIGNAL HOUR:",
        is_signal_hour(
            now
        )
    )

    print(
        "NEXT SIGNAL:",
        next_signal_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )
