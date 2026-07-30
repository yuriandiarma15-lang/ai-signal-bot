import asyncio

from aiogram import Router, F
from aiogram.types import Message

from config.settings import ADMIN_USERNAME

from services.membership import (
    get_active_members
)


router = Router()



# ==========================
# CHECK ADMIN
# ==========================

def is_admin(username):

    if not username:
        return False

    return (
        username.lower()
        ==
        ADMIN_USERNAME.replace("@", "").lower()
    )



# ==========================
# ADMIN PANEL
# ==========================

@router.message(
    F.text == "/admin"
)
async def admin_panel(message: Message):

    if not is_admin(
        message.from_user.username
    ):
        return


    members = get_active_members()


    await message.answer(

        f"""
🛠 <b>ADMIN PANEL</b>

━━━━━━━━━━━━━━

🟢 Member Aktif:

<b>{len(members)}</b>

━━━━━━━━━━━━━━

Bot Signal XAU AI Assistant
""",

        parse_mode="HTML"

    )



# ==========================
# TEST SIGNAL
# ==========================

@router.message(
    F.text.startswith("/testsignal")
)
async def test_signal(message: Message):

    if not is_admin(
        message.from_user.username
    ):
        return



    text = message.text.replace(
        "/testsignal",
        ""
    ).strip()



    if not text:

        await message.answer(
            "Masukkan text signal"
        )

        return



    members = get_active_members()


    total = 0



    for member in members:

        try:

            await message.bot.send_message(

                chat_id=int(
                    member["Telegram ID"]
                ),

                text=text,

                parse_mode="HTML"

            )


            total += 1



            # jeda agar tidak spam Telegram

            await asyncio.sleep(2)



        except Exception as e:

            print(
                "Gagal kirim:",
                e
            )





    await message.answer(

        f"""
✅ <b>TEST SIGNAL TERKIRIM</b>

Jumlah member:

<b>{total}</b>
""",

        parse_mode="HTML"

    )



# ==========================
# SEND PERSONAL USER ID
# MULTIPLE USER + PHOTO
# ==========================

@router.message(
    F.text.startswith("/sent") |
    F.caption.startswith("/sent")
)
async def send_personal(
    message: Message
):


    if not is_admin(
        message.from_user.username
    ):
        return



    data = (

        message.text

        if message.text

        else message.caption

    )



    data = data.replace(
        "/sent",
        ""
    ).strip()



    if not data:


        await message.answer(

            """
Format:

/sent USER_ID1,USER_ID2 PESAN


Contoh:

/sent 1305881282,987654321 Halo member
"""

        )

        return




    split = data.split(
        " ",
        1
    )



    if len(split) < 2:


        await message.answer(

            """
Format salah.

Gunakan:

/sent USER_ID1,USER_ID2 PESAN
"""

        )

        return




    user_ids = split[0].split(",")

    text = split[1]



    total = 0



    for user_id in user_ids:


        user_id = user_id.strip()



        try:



            # Jika ada gambar

            if message.photo:


                await message.bot.send_photo(

                    chat_id=int(user_id),

                    photo=message.photo[-1].file_id,

                    caption=text,

                    parse_mode="HTML"

                )


            else:


                await message.bot.send_message(

                    chat_id=int(user_id),

                    text=text,

                    parse_mode="HTML"

                )



            total += 1



            print(
                "Terkirim:",
                user_id
            )



            # jeda antar user

            await asyncio.sleep(2)



        except Exception as e:


            print(

                "Gagal kirim:",

                user_id,

                e

            )




    await message.answer(

        f"""
✅ <b>PESAN SELESAI DIKIRIM</b>

Berhasil:

<b>{total}</b>

Target:

<b>{len(user_ids)}</b>
""",

        parse_mode="HTML"

    )
