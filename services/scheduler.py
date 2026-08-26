"""
XAU AI SIGNAL SCHEDULER

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


TELEGRAM:
REALTIME

MONITOR:
SETIAP 5 MENIT

ENTRY:
MAKSIMAL 20 MENIT

PERFORMANCE:
TP1 / SL

TP2:
USER RESPONSIBILITY


STRATEGY:

M5 Structure
M1 Entry Timing
SMC
Order Block
FVG
Liquidity
BOS / CHoCH
Risk Management
"""

import asyncio
import logging

from datetime import datetime, timedelta

import pytz

from config.settings import TIMEZONE

from services.signal_builder import build_signal

from services.sender import send_signal_to_members

from services.monitor import add_signal


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

def trading_open(dt=None):
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

        # 00:00 - 02:00

        if current_minutes <= 2 * 60:

            return True

        # 07:00 - 23:59

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
# VALID SIGNAL HOUR
# =========================================================

def is_signal_hour(dt=None):
    """
    Signal dibuat setiap awal jam:

    00
    01
    02

    dan

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

    if not trading_open(
        now
    ):

        return False

    hour = now.hour

    if hour in (
        0,
        1,
        2,
    ):

        return True

    if 7 <= hour <= 23:

        return True

    return False


# =========================================================
# SIGNAL HOUR KEY
# =========================================================

def signal_hour_key(dt):
    """
    ID unik untuk satu jam signal.

    Contoh:

    2026082607
    2026082608
    """

    return (
        dt.strftime(
            "%Y%m%d%H"
        )
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
        signal_hour_key(
            _last_signal_time
        )
        ==
        signal_hour_key(
            dt
        )
    )


# =========================================================
# PROCESS SIGNAL
# =========================================================

async def process_signal(
    bot,
    force_current_hour=False,
):
    """
    Membuat dan mengirim signal.

    force_current_hour=True digunakan ketika bot
    baru restart setelah menit 00 tetapi masih
    berada di jam signal.

    Contoh:

    Bot start 07:04

    -> tetap membuat signal 07:00
    -> bukan menunggu 08:00
    """

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

        return False

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

            return False

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

            return False

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        if _already_processed_this_hour(
            now
        ):

            logger.warning(
                "Signal jam %02d sudah diproses. "
                "Skip duplicate.",
                now.hour,
            )

            return False

        # =================================================
        # HEADER
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

            return False

        # =================================================
        # VALIDATE
        # =================================================

        if signal is None:

            logger.warning(
                "build_signal() menghasilkan None."
            )

            return False

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
        # TELEGRAM
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
        # TELEGRAM GAGAL
        # =================================================

        if not telegram_success:

            logger.error(
                "Tidak ada member yang menerima "
                "signal Telegram."
            )

            return False

        # =================================================
        # SAVE SIGNAL TIME
        # =================================================

        _last_signal_time = now

        # =================================================
        # ADD TO MONITOR
        # =================================================

        try:

            monitor_added = await add_signal(
                signal
            )

            if monitor_added:

                logger.info(
                    "MONITOR REGISTERED | "
                    "Signal mulai dipantau."
                )

            else:

                logger.warning(
                    "MONITOR tidak menambahkan signal."
                )

        except Exception:

            logger.exception(
                "Gagal memasukkan signal "
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
            "Monitor  : EVERY 5 MINUTES"
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

        return True

    finally:

        _signal_running = False


# =========================================================
# NEXT SIGNAL TIME
# =========================================================

def next_signal_time():
    """
    Mencari signal berikutnya.

    Contoh:

    07:04
        -> 08:00

    23:04
        -> 00:00

    Sabtu 02:04
        -> Senin 07:00
    """

    now = datetime.now(
        WIB
    )

    target = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    # Selalu cari jam berikutnya
    target += timedelta(
        hours=1
    )

    for _ in range(200):

        if is_signal_hour(
            target
        ):

            return target

        target += timedelta(
            hours=1
        )

    raise RuntimeError(
        "Tidak dapat menemukan "
        "jadwal signal berikutnya."
    )


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

    # =====================================================
    # STARTUP CATCH-UP
    # =====================================================
    #
    # Jika bot restart:
    #
    # 07:00 -> normal
    # 07:04 -> buat signal 07
    # 07:30 -> tetap buat signal 07
    # 07:59 -> tetap buat signal 07
    #
    # Jadi tidak kehilangan signal hanya karena
    # container restart terlambat.
    #
    # =====================================================

    startup_now = datetime.now(
        WIB
    )

    if (
        trading_open(
            startup_now
        )
        and
        is_signal_hour(
            startup_now
        )
    ):

        logger.info(
            "STARTUP CATCH-UP | "
            "Jam signal %02d masih aktif.",
            startup_now.hour,
        )

        await process_signal(
            bot,
            force_current_hour=True,
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

            next_run = next_signal_time()

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
            # TOLERANCE
            # =================================================

            if check_time.minute != 0:

                logger.warning(
                    "Scheduler wake-up bukan menit 00. "
                    "Current=%s",
                    check_time.strftime(
                        "%H:%M:%S"
                    ),
                )

                continue

            # =================================================
            # PROCESS
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
