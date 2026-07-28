from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command


from config.settings import (
    SOURCE_GROUP_ID,
    ADMIN_USERNAME
)


from services.membership import (
    get_active_members
)


from services.scheduler import (
    trading_open
)


from services.signal_builder import (
    build_signal
)



router = Router()





# =====================================
# ADMIN MANUAL SIGNAL
# =====================================


@router.message(
    Command("signal")
)
async def manual_signal(
    message: Message
):


    username = (
        message.from_user.username
        if message.from_user
        else None
    )



    if not username:


        await message.answer(
            "❌ Username Telegram tidak ditemukan"
        )

        return



    if username != ADMIN_USERNAME.replace(
        "@",
        ""
    ):


        await message.answer(
            "❌ Akses ditolak"
        )

        return



    print(
        "ADMIN REQUEST SIGNAL"
    )



    signal = build_signal()



    await message.answer(

        signal,

        parse_mode="HTML"

    )





# =====================================
# RECEIVE SIGNAL FROM OLD SOURCE GROUP
# =====================================


@router.message(
    F.chat.id == SOURCE_GROUP_ID
)
async def receive_signal(
    message: Message
):


    print(
        "\n======================"
    )

    print(
        "=== SIGNAL GROUP MASUK ==="
    )

    print(
        "======================"
    )



    if not trading_open():


        print(
            "DILUAR JAM TRADING"
        )

        return




    if not message.text:


        print(
            "TEXT KOSONG"
        )

        return




    signal_text = message.text



    print(
        "SIGNAL DITERUSKAN:"
    )

    print(
        signal_text
    )




    members = get_active_members()



    print(
        "TOTAL MEMBER:",
        len(members)
    )





    for member in members:


        telegram_id = member.get(
            "telegram_id"
        )



        if not telegram_id:


            continue




        try:


            await message.bot.send_message(

                chat_id=int(
                    telegram_id
                ),

                text=signal_text

            )



            print(
                "TERKIRIM:",
                telegram_id
            )



        except Exception as e:


            print(
                "GAGAL:",
                telegram_id,
                e
            )
