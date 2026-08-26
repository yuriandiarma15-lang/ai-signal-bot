import asyncio
import logging

from aiogram import Bot, Dispatcher

from config.settings import BOT_TOKEN

from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.signal import router as signal_router
from handlers.admin import router as admin_router

from services.scheduler import signal_scheduler
from services.monitor import monitor_loop


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
# BOT
# =========================================================

if not BOT_TOKEN:

    raise RuntimeError(
        "BOT_TOKEN tidak ditemukan. "
        "Periksa file .env"
    )


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
    # SIGNAL SCHEDULER
    # =====================================================

    signal_task = asyncio.create_task(
        signal_scheduler(bot),
        name="signal_scheduler",
    )

    logger.info(
        "⏰ SIGNAL SCHEDULER STARTED"
    )

    # =====================================================
    # MONITOR
    # =====================================================

    monitor_task = asyncio.create_task(
        monitor_loop(bot),
        name="signal_monitor",
    )

    logger.info(
        "📊 SIGNAL MONITOR STARTED"
    )

    logger.info(
        "📈 MARKET ANALYSIS ENGINE ACTIVE"
    )

    logger.info(
        "⏰ AUTO SIGNAL EVERY HOUR ACTIVE"
    )

    logger.info(
        "🔎 MONITOR SCAN EVERY 5 MINUTES"
    )

    logger.info(
        "=========================================="
    )

    try:

        # =================================================
        # TELEGRAM POLLING
        # =================================================

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

        # =================================================
        # STOP MONITOR
        # =================================================

        logger.info(
            "Menghentikan signal monitor..."
        )

        monitor_task.cancel()

        try:

            await monitor_task

        except asyncio.CancelledError:

            pass

        # =================================================
        # CLOSE BOT
        # =================================================

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
