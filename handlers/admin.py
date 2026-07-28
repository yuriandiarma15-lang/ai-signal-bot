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
        ADMIN_USERNAME.replace("@","").lower()
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



        except Exception as e:

            print(
                "Gagal kirim:",
                e
            )





    await message.answer(

        f"""
✅ <b>TEST SIGNAL TERKIRIM</b>

Jumlah member:

{total}
""",

        parse_mode="HTML"

    )





# ==========================
# SEND PERSONAL USER ID
# ==========================

@router.message(
    F.text.startswith("/sent")
)
async def send_personal(
    message: Message
):


    if not is_admin(
        message.from_user.username
    ):
        return



    data = message.text.replace(
        "/sent",
        ""
    ).strip()



    if not data:


        await message.answer(

            """
Format:

/sent USER_ID PESAN

Contoh:

/sent 1305881282 Halo member
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

/sent USER_ID PESAN
"""

        )

        return




    user_id = split[0]

    text = split[1]




    try:


        await message.bot.send_message(

            chat_id=int(user_id),

            text=text,

            parse_mode="HTML"

        )



        await message.answer(

            f"""
✅ Pesan terkirim

User ID:
<code>{user_id}</code>
""",

            parse_mode="HTML"

        )




    except Exception as e:


        await message.answer(

            f"""
❌ Gagal kirim

User ID:
{user_id}

Error:
{e}
"""

        )
