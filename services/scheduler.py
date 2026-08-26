"""
services/scheduler.py

XAU AI SIGNAL SCHEDULER
=======================

SIGNAL:

Senin
    07:00 - 23:00 WIB

Selasa - Jumat
    00:00 - 02:00 WIB
    07:00 - 23:00 WIB

Sabtu
    00:00 - 02:00 WIB

Minggu
    CLOSED


PERFORMANCE:

Dikirim ke CHANNEL TELEGRAM pada:

    04:00 WIB

Performance session:

    07:00 hari sebelumnya
        sampai
    02:00 hari ini


FLOW:

SIGNAL
    ↓
build_signal()
    ↓
Telegram realtime
    ↓
save pending website
    ↓
website publish +1 JAM


PERFORMANCE

07:00 - 02:00
    ↓
monitor
    ↓
save result
    ↓
04:00
    ↓
build performance
    ↓
Telegram CHANNEL
"""

import asyncio
import logging

from datetime import datetime, timedelta

import pytz

from config.settings import (
    TIMEZONE,
    PERFORMANCE_CHANNEL_ID,
)

from services.signal_builder import (
    build_signal,
)

from services.sender import (
    send_signal_to_members,
)

from services.pending import (
    save_pending_signal,
)

from services.performance import (
    build_session_performance_text,
    mark_performance_sent,
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
# PERFORMANCE LOCK
# =========================================================

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

        # 00:00 - 02:00

        if current_minutes <= 120:

            return True

        # 07:00 - 23:59

        if current_minutes >= 420:

            return True

        return False

    # =====================================================
    # SATURDAY
    # =====================================================

    if weekday == 5:

        return (
            current_minutes <= 120
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

    return (
        hour in (
            0,
            1,
            2,
        )
        or
        7 <= hour <= 23
    )


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
        now.hour == 4
        and
        now.minute == 0
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
# PROCESS SIGNAL
# =========================================================

async def process_signal(
    bot,
):

    global _signal_running
    global _last_signal_time

    if _signal_running:

        logger.warning(
            "Signal sebelumnya masih diproses."
        )

        return

    _signal_running = True

    try:

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
        # BUILD
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

            result = await send_signal_to_members(
                bot,
                signal,
            )

            logger.info(
                "TELEGRAM RESULT: %s",
                result,
            )

            if isinstance(
                result,
                dict,
            ):

                telegram_success = (
                    result.get(
                        "success",
                        0,
                    ) > 0
                )

            else:

                telegram_success = bool(
                    result
                )

        except Exception:

            logger.exception(
                "Telegram send error."
            )

        # =================================================
        # FAILED
        # =================================================

        if not telegram_success:

            logger.error(
                "Signal tidak berhasil dikirim "
                "ke member."
            )

            return

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

        logger.info(
            "SIGNAL PROCESS COMPLETE | "
            "Telegram=REALTIME | "
            "Website=+1 JAM"
        )

        logger.info(
            "=========================================="
        )

    finally:

        _signal_running = False


# =========================================================
# PERFORMANCE
# =========================================================

async def process_performance(
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
        # ONLY 04:00
        # =================================================

        if not is_performance_hour(
            now
        ):

            return

        session_date = (
            now.date()
        )

        # =================================================
        # DUPLICATE
        # =================================================

        if (
            _last_performance_date
            == session_date
        ):

            logger.warning(
                "Performance %s sudah dikirim.",
                session_date,
            )

            return

        # =================================================
        # CHANNEL CHECK
        # =================================================

        if not PERFORMANCE_CHANNEL_ID:

            logger.error(
                "PERFORMANCE_CHANNEL_ID belum "
                "dikonfigurasi."
            )

            return

        logger.info(
            "=========================================="
        )

        logger.info(
            "BUILDING DAILY PERFORMANCE"
        )

        logger.info(
            "Performance time: %s",
            now.strftime(
                "%d-%m-%Y %H:%M:%S WIB"
            ),
        )

        # =================================================
        # BUILD
        # =================================================

        try:

            text = await asyncio.to_thread(
                build_session_performance_text,
                now.date(),
            )

        except Exception:

            logger.exception(
                "Gagal membuat performance text."
            )

            return

        if not text:

            logger.warning(
                "Performance text kosong."
            )

            return

        # =================================================
        # SEND CHANNEL
        # =================================================

        try:

            await bot.send_message(
                chat_id=PERFORMANCE_CHANNEL_ID,
                text=text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )

        except Exception:

            logger.exception(
                "Gagal mengirim performance "
                "ke channel."
            )

            return

        # =================================================
        # MARK SENT
        # =================================================

        try:

            mark_performance_sent(
                now.date()
            )

        except Exception:

            logger.exception(
                "Performance berhasil dikirim, "
                "tetapi gagal menandai sebagai sent."
            )

        _last_performance_date = (
            session_date
        )

        logger.info(
            "PERFORMANCE CHANNEL SENT | "
            "date=%s",
            session_date,
        )

        logger.info(
            "=========================================="
        )

    finally:

        _performance_running = False


# =========================================================
# SIGNAL + PERFORMANCE LOOP
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
        "Signal     : 07:00 - 23:00"
    )

    logger.info(
        "Extended   : 00:00 - 02:00"
    )

    logger.info(
        "Performance: 04:00 WIB"
    )

    logger.info(
        "Telegram   : REALTIME"
    )

    logger.info(
        "Website    : DELAY +1 JAM"
    )

    logger.info(
        "Entry      : MAX 20 MINUTES"
    )

    logger.info(
        "Timeframe  : M5 Structure + M1 Entry"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            now = datetime.now(
                WIB
            )

            # =================================================
            # PERFORMANCE
            # =================================================
            #
            # Kita cek 04:00 setiap loop.
            #
            # Jika scheduler hidup kembali beberapa detik
            # setelah 04:00, masih bisa ditangani melalui
            # toleransi di bawah.
            # =================================================

            if (
                now.hour == 4
                and
                now.minute == 0
            ):

                await process_performance(
                    bot
                )

            # =================================================
            # SIGNAL
            # =================================================

            if (
                now.minute == 0
                and
                is_signal_hour(
                    now
                )
            ):

                await process_signal(
                    bot
                )

                await asyncio.sleep(
                    2
                )

            # =================================================
            # WAIT
            # =================================================
            #
            # Jangan sleep 1 jam.
            #
            # Loop setiap 10 detik membuat scheduler lebih
            # tahan terhadap restart / delay kecil server.
            # =================================================

            await asyncio.sleep(
                10
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
