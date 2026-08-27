# =========================================================
# handlers/materi.py
#
# XAU AI SMC REAL
# MATERI SMC
#
# FILE LOKAL:
#
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
# BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MATERIALS_DIR = BASE_DIR / "materials"


# =========================================================
# FILE MATERIALS
# =========================================================

VIDEO_FILE = MATERIALS_DIR / "smc_basic.mp4"
PDF_FILE = MATERIALS_DIR / "panduan_smc.pdf"
IMAGE_FILE = MATERIALS_DIR / "smc_cheatsheet.jpg"


# =========================================================
# STARTUP LOG
# =========================================================

logger.info("==========================================")
logger.info("📚 SMC MATERIALS")
logger.info("==========================================")
logger.info("📂 Base directory : %s", BASE_DIR)
logger.info("📂 Materials      : %s", MATERIALS_DIR)

logger.info(
    "🎥 Video : %s | exists=%s",
    VIDEO_FILE,
    VIDEO_FILE.exists(),
)

logger.info(
    "📕 PDF   : %s | exists=%s",
    PDF_FILE,
    PDF_FILE.exists(),
)

logger.info(
    "🖼 Image : %s | exists=%s",
    IMAGE_FILE,
    IMAGE_FILE.exists(),
)

logger.info("==========================================")


# =========================================================
# KEYBOARD
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
# VALIDATE VIDEO
# =========================================================

def validate_video_file(file_path: Path) -> tuple[bool, str]:
    """
    Mengecek apakah file benar-benar memiliki
    signature MP4.

    MP4 biasanya memiliki struktur:

        [size][ftyp]

    'ftyp' biasanya berada di byte 4-8.
    """

    try:

        if not file_path.exists():
            return False, "FILE_NOT_FOUND"

        if not file_path.is_file():
            return False, "NOT_A_FILE"

        size = file_path.stat().st_size

        if size <= 0:
            return False, "EMPTY_FILE"

        # File MP4 normal minimal memiliki header.
        if size < 16:
            return False, "FILE_TOO_SMALL"

        with file_path.open("rb") as f:

            header = f.read(32)

        logger.info(
            "🎥 Video header: %s",
            header[:16],
        )

        # -------------------------------------------------
        # MP4 biasanya memiliki 'ftyp'
        # pada byte 4-8.
        # -------------------------------------------------

        if b"ftyp" not in header[:16]:

            return False, "INVALID_MP4_HEADER"

        return True, "OK"

    except Exception as e:

        logger.exception(
            "❌ Error validating video: %s",
            e,
        )

        return False, "VALIDATION_ERROR"


# =========================================================
# /materi
# =========================================================

@router.message(Command("materi"))
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
        "🎥 Menyiapkan video SMC Basic..."
    )

    # =====================================================
    # CEK FILE
    # =====================================================

    logger.info(
        "🎥 Memeriksa video: %s",
        VIDEO_FILE,
    )

    if not VIDEO_FILE.exists():

        logger.error(
            "❌ VIDEO TIDAK DITEMUKAN: %s",
            VIDEO_FILE,
        )

        await callback.message.answer(
            "❌ *Video SMC tidak ditemukan.*\n\n"
            "File yang dicari:\n"
            "`materials/smc_basic.mp4`",
            parse_mode="Markdown",
        )

        return

    # =====================================================
    # CEK UKURAN
    # =====================================================

    try:

        video_size = VIDEO_FILE.stat().st_size

        video_size_mb = video_size / (
            1024 * 1024
        )

        logger.info(
            "🎥 Video size: %.2f MB",
            video_size_mb,
        )

        if video_size <= 0:

            logger.error(
                "❌ VIDEO KOSONG!"
            )

            await callback.message.answer(
                "❌ *File video kosong.*\n\n"
                "Silakan upload ulang video.",
                parse_mode="Markdown",
            )

            return

    except Exception:

        logger.exception(
            "❌ Gagal membaca ukuran video."
        )

        await callback.message.answer(
            "❌ Gagal membaca file video.",
        )

        return

    # =====================================================
    # VALIDASI HEADER MP4
    # =====================================================

    valid, reason = validate_video_file(
        VIDEO_FILE
    )

    if not valid:

        logger.error(
            "❌ VIDEO TIDAK VALID | reason=%s | file=%s",
            reason,
            VIDEO_FILE,
        )

        await callback.message.answer(
            "❌ *File video tidak valid.*\n\n"
            f"Status: `{reason}`\n\n"
            "Kemungkinan file MP4 rusak atau "
            "file yang tersimpan di server bukan "
            "video MP4 asli.",
            parse_mode="Markdown",
        )

        return

    logger.info(
        "✅ VIDEO VALID | %.2f MB | %s",
        video_size_mb,
        VIDEO_FILE,
    )

    # =====================================================
    # KIRIM VIDEO
    # =====================================================

    try:

        logger.info(
            "🎥 Mengirim SMC Basic kepada user_id=%s",
            callback.from_user.id,
        )

        video = FSInputFile(
            path=VIDEO_FILE,
            filename="smc_basic.mp4",
        )

        await callback.message.answer_video(
            video=video,

            caption=(
                "🎥 *SMC BASIC*\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                "Materi dasar *Smart Money Concept*.\n\n"

                "Pelajari:\n"
                "• Market Structure\n"
                "• Liquidity\n"
                "• BOS\n"
                "• CHoCH\n"
                "• Order Block\n"
                "• Fair Value Gap\n\n"

                "🤖 *XAU AI SMC REAL*"
            ),

            parse_mode="Markdown",

            supports_streaming=True,
        )

        logger.info(
            "✅ VIDEO SMC BERHASIL DIKIRIM | user_id=%s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ GAGAL MENGIRIM VIDEO SMC: %s",
            e,
        )

        await callback.message.answer(
            "❌ *Video SMC gagal dikirim.*\n\n"
            "Telegram mengalami masalah saat "
            "memproses file video.\n\n"
            "Silakan coba kembali.",
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

    if not PDF_FILE.exists():

        logger.error(
            "❌ PDF TIDAK DITEMUKAN: %s",
            PDF_FILE,
        )

        await callback.message.answer(
            "❌ *Panduan SMC tidak ditemukan.*\n\n"
            "Pastikan file berada di:\n"
            "`materials/panduan_smc.pdf`",
            parse_mode="Markdown",
        )

        return

    try:

        logger.info(
            "📕 Mengirim PDF SMC kepada user_id=%s",
            callback.from_user.id,
        )

        document = FSInputFile(
            path=PDF_FILE,
            filename="panduan_smc.pdf",
        )

        await callback.message.answer_document(
            document=document,

            caption=(
                "📕 *PANDUAN SMC*\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                "Panduan *Smart Money Concept* "
                "untuk membantu memahami struktur market.\n\n"

                "Pelajari konsep penting SMC "
                "sebagai referensi analisa XAUUSD.\n\n"

                "🤖 *XAU AI SMC REAL*"
            ),

            parse_mode="Markdown",
        )

        logger.info(
            "✅ PDF SMC BERHASIL DIKIRIM | user_id=%s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ GAGAL MENGIRIM PDF SMC: %s",
            e,
        )

        await callback.message.answer(
            "❌ *Panduan SMC gagal dikirim.*\n\n"
            "Silakan coba kembali.",
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

    if not IMAGE_FILE.exists():

        logger.error(
            "❌ IMAGE TIDAK DITEMUKAN: %s",
            IMAGE_FILE,
        )

        await callback.message.answer(
            "❌ *SMC Cheatsheet tidak ditemukan.*\n\n"
            "Pastikan file berada di:\n"
            "`materials/smc_cheatsheet.jpg`",
            parse_mode="Markdown",
        )

        return

    try:

        logger.info(
            "🖼 Mengirim Cheatsheet kepada user_id=%s",
            callback.from_user.id,
        )

        photo = FSInputFile(
            path=IMAGE_FILE,
            filename="smc_cheatsheet.jpg",
        )

        await callback.message.answer_photo(
            photo=photo,

            caption=(
                "🖼 *SMC CHEATSHEET*\n"
                "━━━━━━━━━━━━━━━━━━\n\n"

                "Ringkasan konsep *Smart Money Concept*.\n\n"

                "Gunakan cheatsheet ini sebagai "
                "referensi cepat ketika melakukan "
                "analisa market.\n\n"

                "🤖 *XAU AI SMC REAL*"
            ),

            parse_mode="Markdown",
        )

        logger.info(
            "✅ CHEATSHEET BERHASIL DIKIRIM | user_id=%s",
            callback.from_user.id,
        )

    except Exception as e:

        logger.exception(
            "❌ GAGAL MENGIRIM CHEATSHEET: %s",
            e,
        )

        await callback.message.answer(
            "❌ *SMC Cheatsheet gagal dikirim.*\n\n"
            "Silakan coba kembali.",
            parse_mode="Markdown",
        )
