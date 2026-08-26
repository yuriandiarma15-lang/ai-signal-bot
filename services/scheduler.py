"""
services/scheduler.py

XAU AI SIGNAL SCHEDULER
=======================

SIGNAL:

07:00 - 23:00 WIB
00:00 - 02:00 WIB

Minggu CLOSED.

FLOW:

Scheduler
    ↓
Build Signal
    ↓
Telegram REALTIME
    ↓
ADD MONITOR
    ↓
Save Pending Website
    ↓
Website +1 JAM


PERFORMANCE:

04:00 WIB
"""

import asyncio
import logging
import os

from datetime import datetime, timedelta

import pytz

from config.settings import TIMEZONE

from services.signal_builder import (
    build_signal,
)

from services.sender import (
    send_signal_to_members,
)

from services.pending import (
    save_pending_signal,
)

from services.monitor import (
    add_signal,
)

from services.performance import (
    build_performance_text,
    delete_performance_file,
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
# PERFORMANCE CHANNEL
# =========================================================

def _get_performance_channel_id():

    value = os.getenv(
        "PERFORMANCE_CHANNEL_ID",
        ""
    ).strip()

    if not value:

        return None

    try:

        return int(
            value
        )

    except (
        ValueError,
        TypeError,
    ):

        logger.error(
            "PERFORMANCE_CHANNEL_ID tidak valid: %s",
            value,
        )

        return None


PERFORMANCE_CHANNEL_ID = (
    _get_performance_channel_id()
)


# =========================================================
# PERFORMANCE
# =========================================================

PERFORMANCE_HOUR = 4


# =========================================================
# LOCKS
# =========================================================

_signal_running = False

_performance_running = False


# =========================================================
# LAST SIGNAL
# =========================================================

_last_signal_time = None


# =========================================================
# LAST PERFORMANCE
# =========================================================

_last_performance_date = None


# =========================================================
# TRADING OPEN
# =========================================================

def trading_open(
    dt=None,
):

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
    # SUNDAY
    # =====================================================

    if weekday == 6:

        return False

    # =====================================================
    # MONDAY
    # =====================================================

    if weekday == 0:

        return (
            current_minutes >= 7 * 60
        )

    # =====================================================
    # TUESDAY - FRIDAY
    # =====================================================

    if weekday in (
        1,
        2,
        3,
        4,
    ):

        if current_minutes <= (
            2 * 60
        ):

            return True

        if current_minutes >= (
            7 * 60
        ):

            return True

        return False

    # =====================================================
    # SATURDAY
    # =====================================================

    if weekday == 5:

        return (
            current_minutes <= 2 * 60
        )

    return False


# =========================================================
# SIGNAL HOUR
# =========================================================

def is_signal_hour(
    dt=None,
):

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
# PERFORMANCE HOUR
# =========================================================

def is_performance_hour(
    dt=None,
):

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

    return (
        now.hour == PERFORMANCE_HOUR
        and
        now.minute == 0
    )


# =========================================================
# NEXT EVENT
# =========================================================

def next_event_time():

    now = datetime.now(
        WIB
    )

    target = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    if target <= now:

        target += timedelta(
            hours=1
        )

    for _ in range(240):

        # -----------------------------------------------
        # PERFORMANCE
        # -----------------------------------------------

        if target.hour == PERFORMANCE_HOUR:

            return target

        # -----------------------------------------------
        # SIGNAL
        # -----------------------------------------------

        if is_signal_hour(
            target
        ):

            return target

        target += timedelta(
            hours=1
        )

    raise RuntimeError(
        "Tidak dapat menemukan event scheduler."
    )


# =========================================================
# NEXT SIGNAL
# =========================================================

def next_signal_time():

    now = datetime.now(
        WIB
    )

    target = now.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    if target <= now:

        target += timedelta(
            hours=1
        )

    for _ in range(240):

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
# DUPLICATE SIGNAL
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
# DUPLICATE PERFORMANCE
# =========================================================

def _performance_already_sent(
    dt: datetime,
) -> bool:

    global _last_performance_date

    if _last_performance_date is None:

        return False

    return (
        _last_performance_date
        == dt.date()
    )


# =========================================================
# DAILY PERFORMANCE
# =========================================================

async def send_daily_performance(
    bot,
):

    global _performance_running
    global _last_performance_date

    if _performance_running:

        logger.warning(
            "Performance sebelumnya masih diproses."
        )

        return

    _performance_running = True

    try:

        now = datetime.now(
            WIB
        )

        # =================================================
        # CHANNEL
        # =================================================

        if not PERFORMANCE_CHANNEL_ID:

            logger.error(
                "PERFORMANCE_CHANNEL_ID belum dikonfigurasi."
            )

            return

        # =================================================
        # DUPLICATE
        # =================================================

        if _performance_already_sent(
            now
        ):

            logger.warning(
                "Performance %s sudah dikirim.",
                now.strftime(
                    "%Y-%m-%d"
                ),
            )

            return

        # =================================================
        # BUILD
        # =================================================

        try:

            performance_text = (
                build_performance_text()
            )

        except Exception:

            logger.exception(
                "Gagal membuat performance text."
            )

            return

        if not performance_text:

            logger.warning(
                "Performance text kosong."
            )

            return

        # =================================================
        # SEND
        # =================================================

        try:

            await bot.send_message(

                chat_id=(
                    PERFORMANCE_CHANNEL_ID
                ),

                text=performance_text,

                parse_mode="Markdown",

                disable_web_page_preview=True,

            )

        except Exception:

            logger.exception(
                "Gagal mengirim performance "
                "ke channel Telegram."
            )

            return

        # =================================================
        # SUCCESS
        # =================================================

        _last_performance_date = (
            now.date()
        )

        logger.info(
            "=========================================="
        )

        logger.info(
            "DAILY PERFORMANCE TERKIRIM"
        )

        logger.info(
            "Channel: %s",
            PERFORMANCE_CHANNEL_ID,
        )

        logger.info(
            "Time: %s",
            now.strftime(
                "%d-%m-%Y %H:%M:%S WIB"
            ),
        )

        logger.info(
            "=========================================="
        )

        # =================================================
        # DELETE
        # =================================================

        try:

            delete_performance_file()

        except Exception:

            logger.exception(
                "Performance berhasil dikirim "
                "tetapi file gagal dihapus."
            )

    finally:

        _performance_running = False


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
            "Signal sebelumnya masih diproses."
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
                "Market CLOSED."
            )

            return

        # =================================================
        # SIGNAL HOUR
        # =================================================

        if not is_signal_hour(
            now
        ):

            logger.info(
                "Bukan jam signal."
            )

            return

        # =================================================
        # DUPLICATE
        # =================================================

        if _already_processed_this_hour(
            now
        ):

            logger.warning(
                "Signal %02d:00 sudah diproses.",
                now.hour,
            )

            return

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
            "Signal time: %s",
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
        # NONE
        # =================================================

        if signal is None:

            logger.warning(
                "build_signal() menghasilkan None."
            )

            return

        # =================================================
        # LOG
        # =================================================

        logger.info(
            "SIGNAL CREATED | "
            "bias=%s | "
            "entry=%s | "
            "order=%s | "
            "pending=%s | "
            "probability=%s%%",
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
        )

        # =================================================
        # TELEGRAM MEMBER
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
                "Telegram send error."
            )

            telegram_success = False

        # =================================================
        # FAILED
        # =================================================

        if not telegram_success:

            logger.error(
                "Tidak ada member menerima signal."
            )

            return

        # =================================================
        # ADD TO MONITOR
        # =================================================

        logger.info(
            "Menambahkan signal ke monitor..."
        )

        try:

            monitor_added = await add_signal(
                signal
            )

        except Exception:

            logger.exception(
                "Gagal menambahkan signal ke monitor."
            )

            monitor_added = False

        if monitor_added:

            logger.info(
                "MONITOR ADD SUCCESS | "
                "Signal aktif dalam monitoring."
            )

        else:

            logger.error(
                "MONITOR ADD FAILED | "
                "Signal TIDAK masuk monitoring."
            )

        # =================================================
        # MARK PROCESSED
        # =================================================

        _last_signal_time = now

        # =================================================
        # WEBSITE
        # =================================================

        try:

            save_pending_signal(
                signal
            )

            logger.info(
                "PENDING WEBSITE SAVED | "
                "Publish +1 JAM."
            )

        except Exception:

            logger.exception(
                "Gagal menyimpan pending signal."
            )

        # =================================================
        # COMPLETE
        # =================================================

        logger.info(
            "SIGNAL PROCESS COMPLETE | "
            "Telegram REALTIME | "
            "Monitor ACTIVE | "
            "Website +1 JAM | "
            "Pending timeout 20 menit"
        )

    finally:

        _signal_running = False


# =========================================================
# MAIN SCHEDULER
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
        "Signal       : 07:00 - 23:00"
    )

    logger.info(
        "Extended     : 00:00 - 02:00"
    )

    logger.info(
        "Performance  : 04:00 WIB"
    )

    logger.info(
        "Telegram     : REALTIME"
    )

    logger.info(
        "Website      : DELAY +1 JAM"
    )

    logger.info(
        "Entry        : MAX 20 MINUTES"
    )

    logger.info(
        "Monitor      : ACTIVE"
    )

    logger.info(
        "Monitor Scan : EVERY 5 MINUTES"
    )

    logger.info(
        "Performance Channel: %s",
        PERFORMANCE_CHANNEL_ID,
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            # =================================================
            # CURRENT
            # =================================================

            now = datetime.now(
                WIB
            )

            # =================================================
            # NEXT EVENT
            # =================================================

            next_run = next_event_time()

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
                "NEXT EVENT: %s",
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
            # WAKE
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
                    "Wake-up bukan menit 00."
                )

                continue

            # =================================================
            # PERFORMANCE 04:00
            # =================================================

            if check_time.hour == (
                PERFORMANCE_HOUR
            ):

                await send_daily_performance(
                    bot
                )

                await asyncio.sleep(
                    2
                )

                continue

            # =================================================
            # SIGNAL
            # =================================================

            if is_signal_hour(
                check_time
            ):

                await process_signal(
                    bot
                )

                await asyncio.sleep(
                    2
                )

                continue

            # =================================================
            # NOTHING
            # =================================================

            logger.info(
                "Tidak ada event pada jam ini."
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
        "PERFORMANCE HOUR:",
        is_performance_hour(
            now
        )
    )

    print(
        "NEXT SIGNAL:",
        next_signal_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )

    print(
        "NEXT EVENT:",
        next_event_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )
