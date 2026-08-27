# =========================================================
# handlers/materi.py
#
# XAU AI SMC REAL
# MATERI SMC
# =========================================================

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

logger = logging.getLogger(__name__)

router = Router()


# =========================================================
# CONFIG GITHUB
# =========================================================
#
# CONTOH:
#
# https://raw.githubusercontent.com/USERNAME/REPOSITORY/main/materi
#
# GANTI:
# USERNAME
# REPOSITORY
#
# =========================================================

GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/"
    "USERNAME/REPOSITORY/main/materi"
)


# =========================================================
# FILE MATERI
# =========================================================

VIDEO_URL = (
    f"{GITHUB_RAW_BASE}/smc_basic.mp4"
)

PDF_URL = (
    f"{GITHUB_RAW_BASE}/panduan_smc.pdf"
)

IMAGE_URL = (
    f"{GITHUB_RAW_BASE}/smc_cheatsheet.jpg"
)


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

        "Pelajari Smart Money Concept "
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
# 🎥 VIDEO
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

    try:

        await callback.message.answer_video(
            video=VIDEO_URL,
            caption=(
                "🎥 *SMC BASIC*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Materi dasar Smart Money Concept.\n\n"
                "🤖 XAU AI SMC REAL"
            ),
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Gagal mengirim video SMC."
        )

        await callback.message.answer(
            "❌ Video SMC belum dapat dikirim.\n"
            "Pastikan file dan URL GitHub sudah benar."
        )


# =========================================================
# 📕 PDF
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

    try:

        await callback.message.answer_document(
            document=PDF_URL,
            caption=(
                "📕 *PANDUAN SMC*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Panduan Smart Money Concept "
                "untuk membantu memahami struktur market.\n\n"
                "🤖 XAU AI SMC REAL"
            ),
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Gagal mengirim PDF SMC."
        )

        await callback.message.answer(
            "❌ PDF belum dapat dikirim.\n"
            "Pastikan file dan URL GitHub sudah benar."
        )


# =========================================================
# 🖼 IMAGE
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

    try:

        await callback.message.answer_photo(
            photo=IMAGE_URL,
            caption=(
                "🖼 *SMC CHEATSHEET*\n"
                "━━━━━━━━━━━━━━━━━━\n"
                "Ringkasan konsep Smart Money Concept.\n\n"
                "🤖 XAU AI SMC REAL"
            ),
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Gagal mengirim gambar SMC."
        )

        await callback.message.answer(
            "❌ Cheatsheet belum dapat dikirim.\n"
            "Pastikan file dan URL GitHub sudah benar."
        )
