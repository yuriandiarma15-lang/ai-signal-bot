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


CATATAN WEBSITE:

Signal dibuat pada jam trading asli.

Website menggunakan delay +1 JAM.

Contoh:

Sabtu 00:00 -> website 01:00
Sabtu 01:00 -> website 02:00
Sabtu 02:00 -> website 03:00

Jadi tampilan website Sabtu dapat berjalan
sampai jam 03:00 WIB.

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


from config.settings import (
    TIMEZONE,
)


from services.signal_builder import (
    build_signal,
)


from services.sender import (
    send_signal_to_members,
)


from services.website import (
    send_signal_to_website,
)


from services.pending import (
    save_pending_signal,
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

    # =====================================================
    # JAM MALAM
    # =====================================================

    if hour in (
        0,
        1,
        2,
    ):

        return True

    # =====================================================
    # JAM SIANG / MALAM
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
    # MULAI DARI AWAL JAM BERIKUTNYA
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
    # CARI WAKTU VALID
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
        "Tidak dapat menemukan jadwal signal berikutnya."
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
        # HANYA PROSES PADA JAM SIGNAL
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
                website_result,
            )

        except TypeError:

            try:

                website_result = (
                    await asyncio.to_thread(
                        send_signal_to_website,
                        signal,
                    )
                )

                logger.info(
                    "WEBSITE RESULT: %s",
                    website_result,
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
        # SAVE PENDING
        # =================================================

        try:

            save_pending_signal(
                signal
            )

            logger.info(
                "Signal disimpan ke pending "
                "website (+1 JAM)."
            )

        except Exception:

            logger.exception(
                "Gagal menyimpan pending signal."
            )

        # =================================================
        # COMPLETE
        # =================================================

        logger.info(
            "SIGNAL PROCESS COMPLETE"
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
        "Selasa-Jumat: 00:00 - 02:00 + 07:00 - 23:00 WIB"
    )

    logger.info(
        "Sabtu       : 00:00 - 02:00 WIB"
    )

    logger.info(
        "Minggu      : CLOSED"
    )

    logger.info(
        "Website     : Delay +1 JAM"
    )

    logger.info(
        "Timeframe   : M5 Structure + M1 Entry"
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
            # TOLERANSI WAKE-UP
            # =================================================

            # Scheduler normalnya bangun sekitar :00.
            #
            # Kita izinkan keterlambatan sampai 59 detik.
            #
            # Jadi misalnya:
            #
            # 02:00:03 -> VALID
            # 02:00:20 -> VALID
            # 02:00:55 -> VALID
            #
            # Tetapi jika sistem bangun 02:01:30,
            # jadwal tersebut dilewati dan mencari jam berikutnya.

            if check_time.minute != 0:

                logger.warning(
                    "Scheduler bangun bukan pada menit 00. "
                    "Current=%s. Mencari jadwal berikutnya.",
                    check_time.strftime(
                        "%H:%M:%S"
                    ),
                )

                continue

            # =================================================
            # SESSION
            # =================================================

            if not trading_open(
                check_time
            ):

                logger.info(
                    "Market CLOSED saat scheduler wake-up."
                )

                continue

            # =================================================
            # SIGNAL HOUR
            # =================================================

            if not is_signal_hour(
                check_time
            ):

                logger.info(
                    "Bukan jam signal."
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
