from aiogram import Router

from aiogram.filters import CommandStart

from aiogram.types import (
    Message,
    FSInputFile
)

from services.membership import check_member

from keyboards.reply import main_keyboard

import os



router = Router()





# ==========================
# START COMMAND
# ==========================


@router.message(
    CommandStart()
)

async def start(
    message: Message
):


    user_id = message.from_user.id


    member = check_member(
        user_id
    )





    # ==========================
    # USER BARU
    # BELUM ADA DI SHEET
    # ==========================


    if not member["found"]:



        welcome_image = "assets/welcome.jpg"



        if os.path.exists(
            welcome_image
        ):


            await message.answer_photo(

                photo=FSInputFile(
                    welcome_image
                ),

                caption=f"""

🤖 <b>XAU AI ASSISTANT</b>


Halo <b>{message.from_user.first_name}</b> 👋


Selamat datang di
AI Trading Assistant Anda.


<blockquote>
"Saya akan membantu memberikan
Signal XAUUSD dengan metode
Smart Money Concept
Setiap 1 jam sekali di Menit 00"
</blockquote>


""",

                parse_mode="HTML"

            )






        lot_image = "assets/lot_size.jpg"



        if os.path.exists(
            lot_image
        ):


            await message.answer_photo(

                photo=FSInputFile(
                    lot_image
                ),

                caption="""

📚 <b>MONEY MANAGEMENT GUIDE</b>


Sebelum mengikuti signal,
gunakan lot sesuai modal
dan risiko Anda.


<blockquote>
"Protect your capital first,
profit will follow."
</blockquote>


⚠️ Hindari over lot.


""",

                parse_mode="HTML"

            )







        await message.answer(

f"""

🤖 <b>XAU AI ASSISTANT PREMIUM</b>


Halo <b>{message.from_user.first_name}</b> 👋


Saya adalah AI Assistant pribadi Anda.


Saya akan memberikan:


📊 Signal XAUUSD

🧠 Smart Money Concept Analysis

📈 Market Structure

💎 Liquidity Analysis


━━━━━━━━━━━━━━


⏰ Jadwal Signal:


Setiap 1 jam sekali

Menit 00


━━━━━━━━━━━━━━


Untuk mengaktifkan akses premium,
silahkan lakukan membership.


Gunakan:

<b>/menu</b>


🤖 XAU AI ASSISTANT


""",

            reply_markup=main_keyboard(),

            parse_mode="HTML"

        )


        return







    # ==========================
    # USER SUDAH ADA
    # TAPI EXPIRED
    # ==========================


    if not member["active"]:



        await message.answer(

f"""

🔒 <b>MEMBERSHIP SUDAH HABIS</b>


Halo <b>{message.from_user.first_name}</b> 👋


Masa aktif membership Anda
telah selesai.


━━━━━━━━━━━━━━


Akses premium dihentikan:


📊 XAUUSD Signal

🧠 Smart Money Concept

⚡ Gold Market Update


━━━━━━━━━━━━━━


Silahkan perpanjang membership
untuk mengaktifkan kembali.


Hubungi:


🤖 <b>@Intradayxauusd_bot</b>


━━━━━━━━━━━━━━


<b>XAU AI ASSISTANT</b>


""",

            reply_markup=main_keyboard(),

            parse_mode="HTML"

        )


        return







    # ==========================
    # MEMBER MASIH AKTIF
    # ==========================



    await message.answer(

f"""

🤖 <b>XAU AI ASSISTANT</b>


Halo <b>{message.from_user.first_name}</b> 👋


Saya adalah Assistant pribadi Anda.


🟢 <b>Membership masih aktif</b>


━━━━━━━━━━━━━━


📦 Paket:

<b>{member['package']}</b>


📅 Aktif sampai:

<b>{member['expired']}</b>


━━━━━━━━━━━━━━


Signal XAUUSD akan dikirim
otomatis setiap 1 jam sekali
pada menit 00.


Gunakan:


<b>/menu</b>


untuk melihat layanan Anda.


🤖 <b>XAU AI ASSISTANT</b>


""",

        reply_markup=main_keyboard(),

        parse_mode="HTML"

    )
