from aiogram import Router, F

from aiogram.types import (
    Message,
    CallbackQuery
)


from services.membership import check_member


from keyboards.menu import member_menu


from keyboards.buttons import renew_button




router = Router()





# ==========================
# COMMAND /MENU
# ==========================


@router.message(
    F.text == "/menu"
)

async def menu(
    message: Message
):


    user_id = message.from_user.id


    member = check_member(
        user_id
    )





    # ==========================
    # EXPIRED
    # ==========================


    if not member["active"]:


        text = f"""

🔒 <b>MEMBERSHIP SUDAH BERAKHIR</b>


Halo <b>{message.from_user.first_name}</b> 👋


<blockquote>
"Masa aktif membership Anda
telah selesai."
</blockquote>


━━━━━━━━━━━━━━


Saat ini Anda tidak mendapatkan:


📊 XAUUSD Premium Signal

🧠 Smart Money Concept Analysis

⚡ Gold Market Update


━━━━━━━━━━━━━━


Silakan lakukan perpanjangan
membership untuk mengaktifkan
kembali akses Anda.


Hubungi:


🤖 <b>@Intradayxauusd_bot</b>


"""


        await message.answer(

            text,

            reply_markup=renew_button(),

            parse_mode="HTML"

        )


        return







    # ==========================
    # ACTIVE
    # ==========================


    text = f"""

⚙️ <b>MEMBER MENU</b>


Halo <b>{message.from_user.first_name}</b> 👋


<blockquote>
"Selamat datang kembali.
Akses premium Anda masih aktif."
</blockquote>


━━━━━━━━━━━━━━


🟢 <b>Status:</b>

ACTIVE


📦 <b>Paket:</b>

{member['package']}


📅 <b>Expired:</b>

{member['expired']}


━━━━━━━━━━━━━━


Silakan pilih layanan Anda.


🤖 <b>XAU AI ASSISTANT</b>


"""


    await message.answer(

        text,

        reply_markup=member_menu(),

        parse_mode="HTML"

    )









# ==========================
# CEK EXPIRED BUTTON
# ==========================


@router.callback_query(

    F.data=="check_expired"

)

async def check_expired(

    callback: CallbackQuery

):


    user_id = callback.from_user.id


    member = check_member(
        user_id
    )




    if member["active"]:


        text = f"""

⏳ <b>MEMBERSHIP STATUS</b>


🟢 <b>Status:</b>

ACTIVE


📦 <b>Paket:</b>

{member['package']}


📅 <b>Expired:</b>

{member['expired']}


━━━━━━━━━━━━━━


Terima kasih telah menjadi
bagian dari:


🤖 <b>XAU AI ASSISTANT</b>


"""



        keyboard = member_menu()



    else:


        text = """

🔒 <b>MEMBERSHIP SUDAH BERAKHIR</b>


<blockquote>
"Masa aktif membership Anda
telah selesai."
</blockquote>


Silakan lakukan perpanjangan
untuk mendapatkan kembali:


📊 Signal XAUUSD Premium

🧠 Smart Money Concept

⚡ Market Update Gold


🤖 @Intradayxauusd_bot


"""


        keyboard = renew_button()





    await callback.message.answer(

        text,

        reply_markup=keyboard,

        parse_mode="HTML"

    )


    await callback.answer()
