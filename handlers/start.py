from aiogram import Router

from aiogram.filters import CommandStart

from aiogram.types import Message

from services.membership import check_member

from keyboards.reply import main_keyboard


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


        await message.answer(

            f"""
🔒 <b>ANDA BELUM MENGAKTIFKAN
AI ASSISTANT GOLD</b>


Halo <b>{message.from_user.first_name}</b> 👋


Saat ini Anda belum mengaktifkan
AI Assistant Gold.


━━━━━━━━━━━━━━


Silahkan Aktifkan
AI Assistant Gold Anda Disini:


🌐 <b>signalxau-ai.com</b>

🤖 <b>@Intradayxauusd_bot</b>


━━━━━━━━━━━━━━


Setelah membership aktif,
Anda akan mendapatkan akses
ke layanan AI Assistant Gold.


🤖 <b>XAU AI ASSISTANT GOLD</b>
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
