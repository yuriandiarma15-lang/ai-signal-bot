import asyncio
import logging

from datetime import datetime, timedelta

import pytz

from config.settings import (
    TIMEZONE,
    SMC_PENDING_TIMEOUT_MINUTES,
)

from services.signal_builder import build_signal
from services.sender import send_signal_to_members
from services.website import send_signal_to_website
from services.pending import save_pending_signal


# =========================================================
# TIMEZONE
# =========================================================

WIB = pytz.timezone(
    TIMEZONE
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    "signal_scheduler"
)


# =========================================================
# SIGNAL LOCK
# =========================================================

_signal_running = False


# =========================================================
# TRADING SESSION
# =========================================================

def trading_open(
    dt=None
):
    """
    Cek apakah market XAUUSD sedang dalam
    jam operasional bot.

    Aktif:

    Senin
        07:00 -> 23:59

    Selasa-Jumat
        00:00 -> 02:15
        07:00 -> 23:59

    Sabtu
        00:00 -> 02:15

    Minggu
        CLOSED
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

    weekday = now.weekday()

    current_minutes = (
        now.hour * 60
        + now.minute
    )

    morning_start = (
        7 * 60
    )

    night_end = (
        2 * 60
        + 15
    )

    # =====================================================
    # MINGGU
    # =====================================================

    if weekday == 6:
        return False

    # =====================================================
    # SABTU
    # =====================================================

    if weekday == 5:

        return (
            current_minutes
            <= night_end
        )

    # =====================================================
    # SENIN
    # =====================================================

    if weekday == 0:

        if (
            current_minutes
            < morning_start
        ):
            return False

        return True

    # =====================================================
    # SELASA - JUMAT
    # =====================================================

    if weekday in (
        1,
        2,
        3,
        4
    ):

        # 00:00 - 02:15
        if (
            current_minutes
            <= night_end
        ):
            return True

        # 07:00 - 23:59
        if (
            current_minutes
            >= morning_start
        ):
            return True

    return False


# =========================================================
# NEXT SIGNAL TIME
# =========================================================

def next_signal_time():

    now = datetime.now(
        WIB
    )

    # Mulai dari jam berikutnya
    target = now.replace(
        minute=0,
        second=0,
        microsecond=0
    )

    if target <= now:
        target += timedelta(
            hours=1
        )

    while True:

        weekday = target.weekday()

        current_minutes = (
            target.hour * 60
            + target.minute
        )

        morning_start = (
            7 * 60
        )

        night_end = (
            2 * 60
            + 15
        )

        # =================================================
        # MINGGU
        # =================================================

        if weekday == 6:

            target = (
                target
                + timedelta(days=1)
            ).replace(
                hour=7,
                minute=0,
                second=0,
                microsecond=0
            )

            continue

        # =================================================
        # SABTU
        # =================================================

        if weekday == 5:

            if (
                current_minutes
                > night_end
            ):

                target = (
                    target
                    + timedelta(days=2)
                ).replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                continue

        # =================================================
        # SENIN
        # =================================================

        if weekday == 0:

            if (
                current_minutes
                < morning_start
            ):

                target = target.replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                break

        # =================================================
        # SELASA - JUMAT
        # =================================================

        if weekday in (
            1,
            2,
            3,
            4
        ):

            # 02:16 - 06:59
            if (
                night_end
                < current_minutes
                < morning_start
            ):

                target = target.replace(
                    hour=7,
                    minute=0,
                    second=0,
                    microsecond=0
                )

                break

        # =================================================
        # PASTIKAN TARGET VALID
        # =================================================

        if trading_open(
            target
        ):
            break

        target += timedelta(
            hours=1
        )

    return target


# =========================================================
# BUILD + SEND SIGNAL
# =========================================================

async def process_signal(
    bot
):
    """
    Generate signal -> Telegram -> Website.

    Tidak menggunakan BlockingScheduler,
    sehingga aman dipakai bersama aiogram.
    """

    global _signal_running

    # =====================================================
    # PREVENT DUPLICATE
    # =====================================================

    if _signal_running:

        logger.warning(
            "Signal sebelumnya masih diproses. "
            "Job ini dilewati."
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
                "Market session closed. "
                "Signal tidak dibuat."
            )

            return

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
            )
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

        if signal is None:

            logger.warning(
                "Build signal menghasilkan None."
            )

            return

        logger.info(
            "SIGNAL CREATED | bias=%s | "
            "entry=%s | order=%s | probability=%s%%",
            getattr(
                signal,
                "bias",
                "-"
            ),
            getattr(
                signal,
                "entry_price",
                "-"
            ),
            getattr(
                signal,
                "order_type",
                "-"
            ),
            getattr(
                signal,
                "probability",
                "-"
            ),
        )

        # =================================================
        # TELEGRAM
        # =================================================

        try:

            telegram_result = (
                await send_signal_to_members(
                    bot,
                    signal
                )
            )

            logger.info(
                "TELEGRAM RESULT: %s",
                telegram_result
            )

        except Exception:

            logger.exception(
                "Telegram send error"
            )

            # Jangan membuat signal website
            # kalau Telegram gagal.
            return

        # =================================================
        # WEBSITE
        # =================================================

        try:

            website_result = (
                await send_signal_to_website(
                    signal
                )
            )

            logger.info(
                "WEBSITE RESULT: %s",
                website_result
            )

        except TypeError:

            # Kalau fungsi website kamu
            # masih synchronous.
            try:

                website_result = (
                    await asyncio.to_thread(
                        send_signal_to_website,
                        signal
                    )
                )

                logger.info(
                    "WEBSITE RESULT: %s",
                    website_result
                )

            except Exception:

                logger.exception(
                    "Website send error"
                )

        except Exception:

            logger.exception(
                "Website send error"
            )

        # =================================================
        # SAVE WEBSITE DELAY +1 HOUR
        # =================================================

        try:

            save_pending_signal(
                signal
            )

            logger.info(
                "Signal disimpan untuk website "
                "dengan delay +1 jam."
            )

        except Exception:

            logger.exception(
                "Gagal menyimpan pending signal."
            )

        logger.info(
            "SIGNAL PROCESS COMPLETE"
        )

        logger.info(
            "=========================================="
        )

    finally:

        _signal_running = False


# =========================================================
# SIGNAL LOOP
# =========================================================

async def signal_scheduler(
    bot
):
    """
    Scheduler utama.

    Signal dibuat setiap H1 close:

    07:00
    08:00
    09:00
    ...
    23:00

    lalu:

    00:00
    01:00
    02:00

    Kemudian kembali ke 07:00.
    """

    logger.info(
        "=========================================="
    )

    logger.info(
        "⏰ XAU AI SIGNAL SCHEDULER ACTIVE"
    )

    logger.info(
        "Schedule: 07:00 - 23:00 WIB"
    )

    logger.info(
        "Extended: 00:00 - 02:00 WIB"
    )

    logger.info(
        "=========================================="
    )

    while True:

        try:

            now = datetime.now(
                WIB
            )

            next_run = (
                next_signal_time()
            )

            wait_seconds = (
                next_run - now
            ).total_seconds()

            logger.info(
                "NEXT SIGNAL: %s",
                next_run.strftime(
                    "%d-%m-%Y %H:%M WIB"
                )
            )

            logger.info(
                "WAIT: %.1f detik",
                max(
                    wait_seconds,
                    0
                )
            )

            # =================================================
            # SLEEP
            # =================================================

            await asyncio.sleep(
                max(
                    wait_seconds,
                    1
                )
            )

            # =================================================
            # CHECK SESSION LAGI
            # =================================================

            check_time = datetime.now(
                WIB
            )

            if not trading_open(
                check_time
            ):

                logger.info(
                    "MARKET SESSION CLOSED "
                    "setelah scheduler wake-up."
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
            #
            # Menghindari loop terlalu cepat
            # akibat perbedaan clock.
            # =================================================

            await asyncio.sleep(
                2
            )

        except asyncio.CancelledError:

            logger.info(
                "Signal scheduler dihentikan."
            )

            raise

        except Exception:

            logger.exception(
                "ERROR DI SIGNAL SCHEDULER"
            )

            # Jangan sampai satu error
            # mematikan scheduler.
            await asyncio.sleep(
                10
            )


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print(
        "Scheduler module."
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
        trading_open()
    )

    print(
        "NEXT SIGNAL:",
        next_signal_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )
