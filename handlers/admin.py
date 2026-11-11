
import asyncio
import logging
import re

from aiogram import Router, F
from aiogram.types import Message
from aiogram.exceptions import TelegramRetryAfter

from config.settings import ADMIN_USERNAME

from services.membership import get_active_members


router = Router()
logger = logging.getLogger(__name__)


# =========================================================
# CONFIG BROADCAST
# =========================================================

BROADCAST_PACKAGES = {
    "6 bulan",
    "12 bulan",
    "1 tahun",
    "3 tahun",
    "36 bulan",
}

BROADCAST_DELAY = 0.05


# =========================================================
# CHECK ADMIN
# =========================================================

def is_admin(username):

    if not username:
        return False

    return (
        username.lower()
        == ADMIN_USERNAME.replace("@", "").lower()
    )


def is_private_admin(message):

    return (
        message.chat.type == "private"
        and is_admin(message.from_user.username)
    )


# =========================================================
# NORMALIZE PACKAGE
# =========================================================

def normalize_package(package):

    if not package:
        return ""

    return " ".join(
        str(package).strip().lower().replace("_", " ").split()
    )


# =========================================================
# GET MEMBER VALUE
# =========================================================

def get_member_value(member, *keys):

    normalized = {
        re.sub(r"[^a-z0-9]", "", str(key).lower()): value
        for key, value in member.items()
    }

    for key in keys:

        lookup = re.sub(
            r"[^a-z0-9]",
            "",
            key.lower()
        )

        value = normalized.get(lookup)

        if value is not None and str(value).strip():
            return value

    return ""


# =========================================================
# GET PREMIUM NEWS MEMBERS
# =========================================================

def get_news_members():

    members = get_active_members()

    # Google Sheets gagal.
    # Jangan melakukan broadcast jika data tidak tersedia.

    if members is None:
        raise RuntimeError(
            "Google Spreadsheet tidak tersedia."
        )

    selected = {}
    
    for member in members:

        telegram_id = str(
            get_member_value(
                member,
                "telegram_id",
                "Telegram ID",
                "user_id"
            )
        ).strip()

        if not telegram_id:
            continue

        # Validasi Telegram ID
        if not telegram_id.isdigit():
            continue

        package = normalize_package(
            get_member_value(
                member,
                "paket",
                "broker",
                "package"
            )
        )

        # Hanya paket yang diizinkan
        if package not in BROADCAST_PACKAGES:
            continue

        # get_active_members() sudah memfilter
        # status ACTIVE dan tanggal expired.

        selected[telegram_id] = member

    return list(selected.values())


# =========================================================
# ADMIN PANEL
# =========================================================

@router.message(F.text == "/admin")
async def admin_panel(message: Message):

    if not is_private_admin(message):
        return

    members = get_active_members()

    if members is None:

        await message.answer(
            "❌ Google Spreadsheet sedang tidak tersedia."
        )
        return

    await message.answer(
        f"""
🛠 <b>ADMIN PANEL</b>

━━━━━━━━━━━━━━

🟢 Member Aktif:
<b>{len(members)}</b>

━━━━━━━━━━━━━━

📢 Broadcast News:
/sentall Text News

📨 Kirim Personal:
/sent USER_ID PESAN

🧪 Test Signal:
/testsignal PESAN

━━━━━━━━━━━━━━

XAU AI SIGNAL BOT
""",
        parse_mode="HTML"
    )


# =========================================================
# TEST SIGNAL
# =========================================================

@router.message(
    F.text.regexp(r"^/testsignal(?:@\w+)?(?:\s|$)")
)
async def test_signal(message: Message):

    if not is_private_admin(message):
        return

    text = re.sub(
        r"^/testsignal(?:@\w+)?",
        "",
        message.text or "",
        count=1
    ).strip()

    if not text:

        await message.answer(
            "Masukkan text signal setelah /testsignal."
        )
        return

    members = get_active_members()

    if members is None:

        await message.answer(
            "❌ Google Spreadsheet tidak tersedia."
        )
        return

    success = 0
    failed = 0

    for member in members:

        user_id = str(
            get_member_value(
                member,
                "telegram_id",
                "Telegram ID",
                "user_id"
            )
        ).strip()

        if not user_id.isdigit():
            continue

        try:

            await message.bot.send_message(
                chat_id=int(user_id),
                text=text
            )

            success += 1

            await asyncio.sleep(2)

        except Exception:

            failed += 1

            logger.exception(
                "Gagal mengirim test signal ke %s",
                user_id
            )

    await message.answer(
        f"""
✅ <b>TEST SIGNAL SELESAI</b>

Berhasil: <b>{success}</b>
Gagal: <b>{failed}</b>
""",
        parse_mode="HTML"
    )


# =========================================================
# SENT ALL - PREMIUM NEWS BROADCAST
# =========================================================

@router.message(
    F.text.regexp(r"^/sentall(?:@\w+)?(?:\s|$)")
)
@router.message(
    F.caption.regexp(r"^/sentall(?:@\w+)?(?:\s|$)")
)
async def sent_all_news(message: Message):

    if not is_private_admin(message):
        return

    # Ambil teks perintah
    command_text = message.text or message.caption or ""

    news_text = re.sub(
        r"^/sentall(?:@\w+)?",
        "",
        command_text,
        count=1
    ).strip()

    # Jika tidak ada teks, gunakan pesan yang di-reply.
    source_message = None

    if not news_text and message.reply_to_message:
        source_message = message.reply_to_message

    elif not news_text:

        await message.answer(
            """
📢 <b>PREMIUM NEWS BROADCAST</b>

Format:

<code>/sentall Text News</code>

Atau:

Reply pesan News kemudian kirim:

<code>/sentall</code>

📦 Penerima:
- 6 Bulan
- 12 Bulan / 1 Tahun
- 3 Tahun / 36 Bulan

🔒 Hanya member ACTIVE.
"""
        )
        return

    # =====================================================
    # AMBIL MEMBER DARI SPREADSHEET
    # =====================================================

    await message.answer(
        "⏳ Mengambil data premium member dari Spreadsheet..."
    )

    try:

        members = await asyncio.to_thread(
            get_news_members
        )

    except Exception:

        logger.exception(
            "Gagal mengambil premium members."
        )

        await message.answer(
            "❌ Broadcast dibatalkan.\n"
            "Google Spreadsheet gagal dibaca."
        )
        return

    if not members:

        await message.answer(
            "⚠️ Tidak ditemukan member premium ACTIVE."
        )
        return

    # =====================================================
    # KONFIRMASI JUMLAH TARGET
    # =====================================================

    success = 0
    failed = 0

    total = len(members)

    await message.answer(
        f"""
📢 <b>NEWS BROADCAST DIMULAI</b>

🎯 Target: <b>{total}</b> member

📦 Paket:
• 6 Bulan
• 12 Bulan
• 1 Tahun
• 3 Tahun
• 36 Bulan

⏳ Sedang mengirim...
""",
        parse_mode="HTML"
    )

    # =====================================================
    # BROADCAST
    # =====================================================

    for member in members:

        user_id = str(
            get_member_value(
                member,
                "telegram_id",
                "Telegram ID",
                "user_id"
            )
        ).strip()

        try:

            # Jika admin reply pesan News,
            # bot meneruskan pesan asli.
            if source_message:

                await message.bot.copy_message(
                    chat_id=int(user_id),
                    from_chat_id=source_message.chat.id,
                    message_id=source_message.message_id
                )

            else:

                await message.bot.send_message(
                    chat_id=int(user_id),
                    text=news_text
                )

            success += 1

        except TelegramRetryAfter as error:

            # Jika Telegram membatasi kecepatan,
            # tunggu sesuai waktu yang ditentukan.
            await asyncio.sleep(
                error.retry_after + 1
            )

            try:

                if source_message:

                    await message.bot.copy_message(
                        chat_id=int(user_id),
                        from_chat_id=source_message.chat.id,
                        message_id=source_message.message_id
                    )

                else:

                    await message.bot.send_message(
                        chat_id=int(user_id),
                        text=news_text
                    )

                success += 1

            except Exception:

                failed += 1

                logger.exception(
                    "Broadcast retry gagal: %s",
                    user_id
                )

        except Exception:

            failed += 1

            logger.exception(
                "Broadcast gagal ke Telegram ID: %s",
                user_id
            )

        await asyncio.sleep(BROADCAST_DELAY)

    # =====================================================
    # REPORT
    # =====================================================

    await message.answer(
        f"""
✅ <b>NEWS BROADCAST SELESAI</b>

━━━━━━━━━━━━━━━━

🎯 Target: <b>{total}</b>

🟢 Berhasil: <b>{success}</b>

🔴 Gagal: <b>{failed}</b>

━━━━━━━━━━━━━━━━

📦 Paket penerima:
• 6 Bulan
• 12 Bulan
• 1 Tahun
• 3 Tahun
• 36 Bulan

🔒 Membership ACTIVE saja.
""",
        parse_mode="HTML"
    )

    logger.info(
        "NEWS BROADCAST FINISHED | total=%s success=%s failed=%s",
        total,
        success,
        failed
    )


# =========================================================
# SENT PERSONAL
# =========================================================

@router.message(
    F.text.regexp(r"^/sent(?:@\w+)?(?:\s|$)")
)
@router.message(
    F.caption.regexp(r"^/sent(?:@\w+)?(?:\s|$)")
)
async def send_personal(message: Message):

    if not is_private_admin(message):
        return

    data = message.text or message.caption or ""

    data = re.sub(
        r"^/sent(?:@\w+)?",
        "",
        data,
        count=1
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

    split = data.split(" ", 1)

    if len(split) < 2:

        await message.answer(
            "Format salah. Gunakan /sent USER_ID PESAN"
        )
        return

    user_ids = split[0].split(",")
    text = split[1]

    success = 0
    failed = 0

    for user_id in user_ids:

        user_id = user_id.strip()

        if not user_id.isdigit():
            failed += 1
            continue

        try:

            if message.photo:

                await message.bot.send_photo(
                    chat_id=int(user_id),
                    photo=message.photo[-1].file_id,
                    caption=text
                )

            else:

                await message.bot.send_message(
                    chat_id=int(user_id),
                    text=text
                )

            success += 1

            await asyncio.sleep(2)

        except Exception:

            failed += 1

            logger.exception(
                "Gagal mengirim pesan personal ke %s",
                user_id
            )

    await message.answer(
        f"""
✅ <b>PESAN PERSONAL SELESAI</b>

Berhasil: <b>{success}</b>
Gagal: <b>{failed}</b>
Target: <b>{len(user_ids)}</b>
""",
        parse_mode="HTML"
    )
