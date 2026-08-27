# =========================================================
# handlers/materi.py
#
# XAU AI SMC REAL
# MATERI SMC
#
# File lokal:
# materials/
# ├── panduan_smc.pdf
# ├── smc_basic.mp4
# └── smc_cheatsheet.jpg
# =========================================================

import logging
from pathlib import Path

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    FSInputFile,
)

logger = logging.getLogger(__name__)

router = Router()


# =========================================================
# PATH MATERIALS
# =========================================================

# Lokasi root project
BASE_DIR = Path(__file__).resolve().parent.parent

# Folder materials
MATERIALS_DIR = BASE_DIR / "materials"


# =========================================================
# FILE MATERI
# =========================================================

VIDEO_FILE = MATERIALS_DIR / "smc_basic.mp4"

PDF_FILE = MATERIALS_DIR / "panduan_smc.pdf"

IMAGE_FILE = MATERIALS_DIR / "smc_cheatsheet.jpg"


# =========================================================
# LOG PATH
# =========================================================

logger.info("📚 Materials directory : %s", MATERIALS_DIR)
logger.info("🎥 SMC Video           : %s", VIDEO_FILE)
logger.info("📕 SMC PDF             : %s", PDF_FILE)
logger.info("🖼 SMC Image           : %s", IMAGE_FILE)


# =========================================================
# MENU MATERI
# =========================================================

def materi_keyboard() -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🎥 SMC BASIC",
                    callback_data="materi_video",
                )
            ],

            [
                InlineKeyboardButton(
                    text="📕 PANDUAN SMC",
                    callback_data="materi_pdf",
                )
            ],

            [
                InlineKeyboardButton(
                    text="🖼 SMC CHEATSHEET",
                    callback_data="materi_image",
                )
            ],

        ]
    )


# =========================================================
# /materi
# =========================================================

@router.message(
    Command("materi")
)
async def materi_command(
    message: Message,
):

    text = (
        "📚 *XAU AI SMC REAL — MATERI*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "Pelajari *Smart Money Concept* "
        "dan tingkatkan pemahaman analisa XAUUSD.\n\n"

        "🎥 *SMC BASIC*\n"
        "Video pembelajaran dasar Smart Money Concept.\n\n"

        "📕 *PANDUAN SMC*\n"
        "Panduan PDF mengenai konsep dan struktur SMC.\n\n"

        "🖼 *SMC CHEATSHEET*\n"
        "Ringkasan konsep SMC dalam satu gambar.\n\n"

        "👇 *Pilih materi yang ingin kamu pelajari:*"
    )

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=materi_keyboard(),
    )


# =========================================================
# 🎥 VIDEO SMC BASIC
# =========================================================

@router.callback_query(
    lambda c: c.data == "materi_video"
)
async def materi_video(
    callback: CallbackQuery,
):

    await callback.answer(
        "🎥 Mengirim video SMC Basic..."
    )

    # -----------------------------------------------------
    # CEK FILE
    # -----------------------------------------------------

    if not VIDEO_FILE.exists():

        logger.error(
            "❌ Video SMC tidak ditemukan: %s",
            VIDEO_FILE,
        )

        await callback.message.answer(
            "❌ *Video SMC tidak ditemukan.*\n\n"
            f"Lokasi yang dicari:\n"
            f"`{VIDEO_FILE}`",
            parse_mode="Markdown",
        )

        return

    # -----------------------------------------------------
    # KIRIM VIDEO
    # -----------------------------------------------------

    try:

        video = FSInputFile(
            path=VIDEO_FILE
        )

        await callback.message.answer_video(
            video=video,
            caption=(
                "🎥 *SMC BASIC*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Materi dasar Smart Money Concept.\n\n"
                "Pelajari struktur market, "
                "liquidity, BOS, CHoCH, OB dan FVG.\n\n"
                "🤖 *XAU AI SMC REAL*"
            ),
            parse_mode="Markdown",
        )

        logger.info(
            "✅ Video SMC berhasil dikirim ke user %s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ Gagal mengirim video SMC: %s",
            e,
        )

        await callback.message.answer(
            "❌ *Video SMC gagal dikirim.*\n\n"
            "File ditemukan, tetapi Telegram gagal "
            "mengirim file tersebut.\n\n"
            "Silakan cek log server.",
            parse_mode="Markdown",
        )


# =========================================================
# 📕 PDF PANDUAN SMC
# =========================================================

@router.callback_query(
    lambda c: c.data == "materi_pdf"
)
async def materi_pdf(
    callback: CallbackQuery,
):

    await callback.answer(
        "📕 Mengirim panduan SMC..."
    )

    # -----------------------------------------------------
    # CEK FILE
    # -----------------------------------------------------

    if not PDF_FILE.exists():

        logger.error(
            "❌ PDF SMC tidak ditemukan: %s",
            PDF_FILE,
        )

        await callback.message.answer(
            "❌ *Panduan SMC tidak ditemukan.*\n\n"
            f"Lokasi yang dicari:\n"
            f"`{PDF_FILE}`",
            parse_mode="Markdown",
        )

        return

    # -----------------------------------------------------
    # KIRIM PDF
    # -----------------------------------------------------

    try:

        document = FSInputFile(
            path=PDF_FILE
        )

        await callback.message.answer_document(
            document=document,
            caption=(
                "📕 *PANDUAN SMC*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Panduan Smart Money Concept "
                "untuk membantu memahami struktur market.\n\n"
                "Materi mencakup konsep penting "
                "dalam analisa SMC.\n\n"
                "🤖 *XAU AI SMC REAL*"
            ),
            parse_mode="Markdown",
        )

        logger.info(
            "✅ PDF SMC berhasil dikirim ke user %s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ Gagal mengirim PDF SMC: %s",
            e,
        )

        await callback.message.answer(
            "❌ *Panduan SMC gagal dikirim.*\n\n"
            "File ditemukan, tetapi Telegram gagal "
            "mengirim file tersebut.\n\n"
            "Silakan cek log server.",
            parse_mode="Markdown",
        )


# =========================================================
# 🖼 SMC CHEATSHEET
# =========================================================

@router.callback_query(
    lambda c: c.data == "materi_image"
)
async def materi_image(
    callback: CallbackQuery,
):

    await callback.answer(
        "🖼 Mengirim SMC Cheatsheet..."
    )

    # -----------------------------------------------------
    # CEK FILE
    # -----------------------------------------------------

    if not IMAGE_FILE.exists():

        logger.error(
            "❌ Image SMC tidak ditemukan: %s",
            IMAGE_FILE,
        )

        await callback.message.answer(
            "❌ *SMC Cheatsheet tidak ditemukan.*\n\n"
            f"Lokasi yang dicari:\n"
            f"`{IMAGE_FILE}`",
            parse_mode="Markdown",
        )

        return

    # -----------------------------------------------------
    # KIRIM IMAGE
    # -----------------------------------------------------

    try:

        photo = FSInputFile(
            path=IMAGE_FILE
        )

        await callback.message.answer_photo(
            photo=photo,
            caption=(
                "🖼 *SMC CHEATSHEET*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Ringkasan konsep Smart Money Concept.\n\n"
                "Gunakan cheatsheet ini sebagai "
                "referensi cepat saat melakukan analisa.\n\n"
                "🤖 *XAU AI SMC REAL*"
            ),
            parse_mode="Markdown",
        )

        logger.info(
            "✅ SMC Cheatsheet berhasil dikirim ke user %s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ Gagal mengirim SMC Cheatsheet: %s",
            e,
        )

        await callback.message.answer(
            "❌ *SMC Cheatsheet gagal dikirim.*\n\n"
            "File ditemukan, tetapi Telegram gagal "
            "mengirim file tersebut.\n\n"
            "Silakan cek log server.",
            parse_mode="Markdown",
        )
