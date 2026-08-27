"""
main.py

XAU AI SIGNAL BOT
=================

Fungsi:
- Menjalankan Telegram Bot
- Register semua handler
- Telegram command menu
- Menjalankan signal scheduler
- Signal Telegram realtime
- Website delay +1 jam

TIDAK MENJALANKAN:
- Entry monitor dari main.py
- TP/SL monitor dari main.py
- Performance monitor dari main.py
"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config.settings import BOT_TOKEN

from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.signal import router as signal_router
from handlers.admin import router as admin_router
from handlers.materi import router as materi_router
from handlers.fundamental import router as fundamental_router

from services.scheduler import signal_scheduler


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "[%(levelname)s] "
        "%(name)s: "
        "%(message)s"
    ),
)

logger = logging.getLogger("main")


# =========================================================
# BOT TOKEN CHECK
# =========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN tidak ditemukan. "
        "Periksa file .env"
    )


# =========================================================
# BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()


# =========================================================
# REGISTER HANDLERS
# =========================================================

dp.include_router(
    start_router
)

dp.include_router(
    menu_router
)

dp.include_router(
    signal_router
)

dp.include_router(
    admin_router
)

dp.include_router(
    materi_router
)

dp.include_router(
    fundamental_router
)


# =========================================================
# TELEGRAM COMMAND MENU
# =========================================================

async def setup_bot_commands():

    await bot.set_my_commands(
        [
            # -------------------------------------------------
            # START
            # -------------------------------------------------

            BotCommand(
                command="start",
                description="Mulai menggunakan bot",
            ),

            # -------------------------------------------------
            # MENU
            # -------------------------------------------------

            BotCommand(
                command="menu",
                description="Buka menu utama",
            ),

            # -------------------------------------------------
            # SIGNAL
            # -------------------------------------------------

            BotCommand(
                command="signal",
                description="Generate signal XAUUSD",
            ),

            # -------------------------------------------------
            # FUNDAMENTAL
            # -------------------------------------------------

            BotCommand(
                command="fundamental",
                description="Analisis fundamental Gold",
            ),

            # -------------------------------------------------
            # MATERI
            # -------------------------------------------------

            BotCommand(
                command="materi",
                description="Materi belajar SMC",
            ),
        ]
    )

    logger.info(
        "📋 Telegram command menu berhasil diperbarui"
    )


# =========================================================
# STARTUP
# =========================================================

async def main():

    logger.info(
        "=========================================="
    )

    logger.info(
        "🤖 XAU AI SIGNAL BOT STARTING..."
    )

    logger.info(
        "=========================================="
    )

    # =====================================================
    # SET TELEGRAM COMMAND
    # =====================================================

    try:

        await setup_bot_commands()

    except Exception:

        logger.exception(
            "Gagal mengatur Telegram command menu."
        )


    # =====================================================
    # SIGNAL SCHEDULER
    #
    # Scheduler bertanggung jawab untuk:
    #
    # - Auto signal
    # - Telegram realtime
    # - Monitor
    # - Website delay
    # - Performance sesuai scheduler
    #
    # Fundamental akan dipanggil dari
    # signal_builder / combined service,
    # bukan dari main.py.
    # =====================================================

    signal_task = asyncio.create_task(
        signal_scheduler(bot),
        name="signal_scheduler",
    )

    logger.info(
        "⏰ SIGNAL SCHEDULER STARTED"
    )


    # =====================================================
    # MONITOR STATUS
    # =====================================================

    logger.info(
        "⛔ SIGNAL MONITOR : DISABLED"
    )

    logger.info(
        "⛔ ENTRY MONITOR  : DISABLED"
    )

    logger.info(
        "⛔ ENTRY TIMEOUT  : DISABLED"
    )

    logger.info(
        "⛔ SL MONITOR     : DISABLED"
    )

    logger.info(
        "⛔ TP1 MONITOR    : DISABLED"
    )

    logger.info(
        "⛔ TP2 MONITOR    : DISABLED"
    )

    logger.info(
        "⛔ PERFORMANCE    : DISABLED"
    )

    logger.info(
        "⛔ 04:00 CHANNEL  : DISABLED"
    )


    # =====================================================
    # ENGINE STATUS
    # =====================================================

    logger.info(
        "📈 MARKET ANALYSIS ENGINE ACTIVE"
    )

    logger.info(
        "⏰ AUTO SIGNAL EVERY HOUR ACTIVE"
    )

    logger.info(
        "📡 TELEGRAM SIGNAL DELIVERY ACTIVE"
    )

    logger.info(
        "📊 DETAIL ANALYSIS AVAILABLE"
    )

    logger.info(
        "📰 FUNDAMENTAL NEWS COMMAND ACTIVE"
    )

    logger.info(
        "📚 SMC MATERIAL AVAILABLE"
    )

    logger.info(
        "=========================================="
    )


    # =====================================================
    # TELEGRAM POLLING
    # =====================================================

    try:

        await dp.start_polling(
            bot
        )


    except asyncio.CancelledError:

        logger.info(
            "Bot menerima shutdown signal."
        )

        raise


    except Exception:

        logger.exception(
            "Telegram polling error."
        )


    finally:

        # =================================================
        # STOP SIGNAL SCHEDULER
        # =================================================

        logger.info(
            "Menghentikan signal scheduler..."
        )

        signal_task.cancel()

        try:

            await signal_task

        except asyncio.CancelledError:

            pass

        except Exception:

            logger.exception(
                "Error saat menghentikan signal scheduler."
            )


        # =================================================
        # CLOSE BOT
        # =================================================

        logger.info(
            "Menutup koneksi Telegram..."
        )

        await bot.session.close()

        logger.info(
            "Bot shutdown selesai."
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    try:

        asyncio.run(
            main()
        )

    except KeyboardInterrupt:

        logger.info(
            "Bot dihentikan manual."
        )
