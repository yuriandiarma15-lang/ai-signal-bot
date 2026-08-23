"""
XAU AI SIGNAL SCHEDULER

Fungsi:
- Generate signal setiap H1 close
- Analisa SMC M5
- Timing entry M1
- Kirim signal ke member aktif
- Simpan signal untuk website delay +1 jam
- Mengikuti jam trading XAUUSD
- Mencegah duplicate signal
- Aman digunakan bersama aiogram asyncio

Jadwal:

Senin:
07:00 - 23:00

Selasa - Jumat:
00:00 - 02:00
07:00 - 23:00

Sabtu:
00:00 - 02:00

Minggu:
CLOSED
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
#
# Pengaman tambahan supaya satu jam tidak menghasilkan
# dua signal karena scheduler wake-up terlalu dekat
# dengan pergantian jam.
# =========================================================

_last_signal_time = None


# =========================================================
# TRADING SESSION
# =========================================================

def trading_open(dt=None):
    """
    Mengecek apakah jam trading XAUUSD sedang aktif.

    Senin:
        07:00 - 23:59

    Selasa - Jumat:
        00:00 - 02:00
        07:00 - 23:59

    Sabtu:
        00:00 - 02:00

    Minggu:
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

    # =====================================================
    # JAM TRADING
    # =====================================================

    morning_start = (
        7 * 60
    )

    night_end = (
        2 * 60
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

        return (
            current_minutes
            >= morning_start
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
    """
    Mengembalikan waktu signal berikutnya.

    Signal hanya dibuat pada H1 close:

    07:00
    08:00
    ...
    23:00

    lalu:

    00:00
    01:00
    02:00

    kemudian kembali 07:00.
    """

    now = datetime.now(
        WIB
    )

    # =====================================================
    # MULAI DARI JAM BERIKUTNYA
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

    while True:

        if trading_open(
            target
        ):

            return target

        # =================================================
        # Kalau belum masuk sesi hari tersebut,
        # lompat satu jam.
        # =================================================

        target += timedelta(
            hours=1
        )

        # =================================================
        # Jika melewati sesi malam,
        # loop akan menemukan 07:00 berikutnya.
        # =================================================


# =========================================================
# DUPLICATE PROTECTION
# =========================================================

def _already_processed_this_hour(
    dt: datetime
) -> bool:
    """
    Mencegah signal dibuat dua kali
    pada jam yang sama.
    """

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
# BUILD + SEND SIGNAL
# =========================================================

async def process_signal(
    bot
):
    """
    Proses utama:

    1. Cek market
    2. Build SMC signal
    3. Kirim Telegram
    4. Kirim/update website
    5. Simpan pending website +1 jam
    """

    global _signal_running
    global _last_signal_time

    # =====================================================
    # PREVENT DUPLICATE PROCESS
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
                "Market session CLOSED. "
                "Signal tidak dibuat."
            )

            return

        # =================================================
        # DUPLICATE CHECK
        # =================================================

        if _already_processed_this_hour(
            now
        ):

            logger.warning(
                "Signal jam %02d sudah pernah "
                "diproses. Skip duplicate.",
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

            # sender baru mengembalikan:
            #
            # {
            #   success: ...,
            #   failed: ...,
            #   total: ...
            # }

            if isinstance(
                telegram_result,
                dict,
            ):

                telegram_success = (
                    telegram_result.get(
                        "success",
                        0
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
        # JIKA TELEGRAM GAGAL TOTAL
        # =================================================

        if not telegram_success:

            logger.error(
                "Tidak ada member yang menerima "
                "signal Telegram."
            )

            # Jangan tandai sebagai signal
            # sukses untuk website.

            return

        # =================================================
        # MARK SIGNAL PROCESSED
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

            # =================================================
            # WEBSITE SYNC FALLBACK
            # =================================================

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
        # SAVE DELAY WEBSITE +1 JAM
        # =================================================

        try:

            save_pending_signal(
                signal
            )

            logger.info(
                "Signal disimpan ke pending "
                "website (+1 jam)."
            )

        except Exception:

            logger.exception(
                "Gagal menyimpan pending signal."
            )

        # =================================================
        # FINAL LOG
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
    bot
):
    """
    Scheduler utama XAU AI.

    Signal:

    07:00
    08:00
    09:00
    ...
    23:00

    kemudian:

    00:00
    01:00
    02:00

    kemudian kembali 07:00.
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
        "Timeframe: M5 Structure + M1 Entry"
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
            # SESSION CHECK
            # =================================================

            if not trading_open(
                check_time
            ):

                logger.info(
                    "Market CLOSED saat scheduler wake-up."
                )

                continue

            # =================================================
            # PASTIKAN BENAR-BENAR DI JAM CLOSE
            # =================================================

            # Scheduler seharusnya bangun sekitar :00.
            #
            # Toleransi 20 detik diberikan supaya tidak
            # gagal karena delay sistem/network.

            if (
                check_time.minute != 0
                and check_time.second > 20
            ):

                logger.warning(
                    "Wake-up tidak berada di awal jam. "
                    "Scheduler mencari jadwal berikutnya."
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

            # Jangan sampai scheduler mati
            # hanya karena satu error.

            await asyncio.sleep(
                10
            )


# =========================================================
# TEST MODULE
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
        trading_open()
    )

    print(
        "NEXT SIGNAL:",
        next_signal_time().strftime(
            "%d-%m-%Y %H:%M WIB"
        )
    )
