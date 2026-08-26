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

Setiap hari:
    04:00 WIB

Performance mencakup:

    Hari sebelumnya 07:00
        sampai
    hari ini 02:00

Contoh:

25-08 07:00
...
25-08 23:00
26-08 00:00
26-08 01:00
26-08 02:00

        ↓

26-08 04:00

Performance dikirim ke Telegram Channel.
"""


import asyncio
import logging

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


from services.performance import (
    send_daily_performance,
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
# LAST SIGNAL TIME
# =========================================================

_last_signal_time = None


# =========================================================
# LAST PERFORMANCE DATE
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
            current_minutes <= (
                2 * 60
            )
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


    # 00:00 - 02:00

    if hour in (
        0,
        1,
        2,
    ):

        return True


    # 07:00 - 23:00

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
        now.hour == 4
        and
        now.minute == 0
    )


# =========================================================
# PERFORMANCE TRADING DATE
# =========================================================

def get_performance_trading_date(
    dt=None,
):
    """
    Menentukan tanggal awal siklus trading.

    Performance jam 04:00:

        26 Agustus 04:00

    mengambil:

        25 Agustus 07:00
        sampai
        26 Agustus 02:00

    Maka trading date = 25 Agustus.
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


    # Pada jam 04:00,
    # trading day dimulai kemarin.

    return (
        now.date()
        - timedelta(
            days=1
        )
    )


# =========================================================
# NEXT SIGNAL TIME
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
# NEXT PERFORMANCE TIME
# =========================================================

def next_performance_time():

    now = datetime.now(
        WIB
    )


    target = now.replace(
        hour=4,
        minute=0,
        second=0,
        microsecond=0,
    )


    if target <= now:

        target += timedelta(
            days=1
        )


    return target


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

def _already_processed_performance(
    trading_date,
) -> bool:

    global _last_performance_date


    if _last_performance_date is None:

        return False


    return (
        _last_performance_date
        == trading_date
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


        # =================================================
        # VALIDATE
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
        # SEND TELEGRAM
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
        # TELEGRAM FAILED
        # =================================================

        if not telegram_success:

            logger.error(
                "Signal tidak berhasil "
                "dikirim ke member."
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
                "PENDING WEBSITE SAVED."
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
            "Telegram=REALTIME | "
            "Website=+1 JAM | "
            "Pending=20 MENIT"
        )


    finally:

        _signal_running = False


# =========================================================
# PROCESS PERFORMANCE
# =========================================================

async def process_performance(
    bot,
):

    global _performance_running
    global _last_performance_date


    # =====================================================
    # LOCK
    # =====================================================

    if _performance_running:

        logger.warning(
            "Performance sebelumnya masih diproses."
        )

        return


    _performance_running = True


    try:

        # =================================================
        # CURRENT TIME
        # =================================================

        now = datetime.now(
            WIB
        )


        # =================================================
        # PERFORMANCE HOUR
        # =================================================

        if not is_performance_hour(
            now
        ):

            return


        # =================================================
        # TRADING DATE
        # =================================================

        trading_date = (
            get_performance_trading_date(
                now
            )
        )


        # =================================================
        # DUPLICATE
        # =================================================

        if _already_processed_performance(
            trading_date
        ):

            logger.warning(
                "Performance %s sudah dikirim.",
                trading_date,
            )

            return


        # =================================================
        # HEADER
        # =================================================

        logger.info(
            "=========================================="
        )

        logger.info(
            "GENERATING DAILY PERFORMANCE"
        )

        logger.info(
            "Trading date: %s",
            trading_date,
        )

        logger.info(
            "Performance time: %s",
            now.strftime(
                "%d-%m-%Y %H:%M:%S WIB"
            ),
        )


        # =================================================
        # SEND
        # =================================================

        success = False


        try:

            success = await send_daily_performance(
                bot,
                target_date=trading_date,
            )

        except Exception:

            logger.exception(
                "Performance send error."
            )

            success = False


        # =================================================
        # SUCCESS
        # =================================================

        if success:

            _last_performance_date = (
                trading_date
            )

            logger.info(
                "DAILY PERFORMANCE TERKIRIM."
            )

        else:

            logger.error(
                "DAILY PERFORMANCE GAGAL TERKIRIM."
            )


    finally:

        _performance_running = False


# =========================================================
# SCHEDULER
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
        "Signal       : 07:00 - 02:00 WIB"
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
        "Pending      : MAX 20 MENIT"
    )

    logger.info(
        "Timeframe    : M5 Structure + M1 Entry"
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
            # PERFORMANCE
            # =================================================

            if is_performance_hour(
                now
            ):

                await process_performance(
                    bot
                )


                # Hindari menjalankan loop berkali-kali
                # pada menit 04:00.

                await asyncio.sleep(
                    60
                )

                continue


            # =================================================
            # NEXT EVENT
            # =================================================

            next_signal = (
                next_signal_time()
            )

            next_performance = (
                next_performance_time()
            )


            # =================================================
            # PILIH EVENT TERDEKAT
            # =================================================

            if next_performance < next_signal:

                next_run = (
                    next_performance
                )

                event_type = (
                    "PERFORMANCE"
                )

            else:

                next_run = (
                    next_signal
                )

                event_type = (
                    "SIGNAL"
                )


            # =================================================
            # WAIT
            # =================================================

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
                "NEXT %s: %s",
                event_type,
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
            # PERFORMANCE
            # =================================================

            if is_performance_hour(
                check_time
            ):

                await process_performance(
                    bot
                )

                continue


            # =================================================
            # SIGNAL
            # =================================================

            if (
                check_time.minute == 0
                and
                is_signal_hour(
                    check_time
                )
            ):

                await process_signal(
                    bot
                )

                await asyncio.sleep(
                    2
                )

                continue


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

    now = datetime.now(
        WIB
    )


    print(
        "=========================================="
    )

    print(
        "XAU AI SIGNAL SCHEDULER TEST"
    )

    print(
        "=========================================="
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
        "TRADING DATE PERFORMANCE:",
        get_performance_trading_date(
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
        "NEXT PERFORMANCE:",
        next_performance_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )
