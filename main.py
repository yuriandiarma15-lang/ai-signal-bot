import asyncio


from aiogram import Bot, Dispatcher


from config.settings import BOT_TOKEN


from handlers.start import router as start_router
from handlers.menu import router as menu_router
from handlers.signal import router as signal_router
from handlers.admin import router as admin_router


from services.scheduler import (
    signal_scheduler
)





# ==========================
# BOT SETUP
# ==========================


bot = Bot(
    token=BOT_TOKEN
)



dp = Dispatcher()





# ==========================
# REGISTER HANDLER
# ==========================


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






# ==========================
# START BOT
# ==========================


async def main():


    print(
        "🤖 XAU AI SIGNAL BOT RUNNING..."
    )



    # ======================
    # START SIGNAL ENGINE
    # ======================


    asyncio.create_task(

        signal_scheduler(
            bot
        )

    )



    print(
        "📊 MARKET ANALYSIS ENGINE ACTIVE"
    )



    print(
        "⏰ AUTO SIGNAL EVERY HOUR ACTIVE"
    )





    await dp.start_polling(

        bot

    )






if __name__ == "__main__":


    asyncio.run(main())
