"""
handlers/fundamental.py

XAU AI SIGNAL BOT
=================

Fungsi:
- Menangani command /fundamental
- Mengambil berita fundamental terbaru
- Menampilkan dampak berita terhadap Gold
- Menampilkan source dan waktu berita
- Tidak mengubah logic SMC
- Tidak mengubah signal builder
- Kompatibel dengan services/fundamental_service.py
"""

import asyncio
import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.fundamental_service import (
    get_latest_fundamental_news,
    format_fundamental_news,
)


# =========================================================
# ROUTER
# =========================================================

router = Router(
    name="fundamental"
)


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    "fundamental_handler"
)


# =========================================================
# COMMAND /FUNDAMENTAL
# =========================================================

@router.message(
    Command("fundamental")
)
async def fundamental_command(
    message: Message,
):
    """
    Command:

        /fundamental

    Mengambil 1 berita fundamental terbaik
    untuk Gold/XAUUSD.
    """

    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "User meminta fundamental | "
        "user_id=%s | "
        "username=%s",
        message.from_user.id
        if message.from_user
        else "-",
        message.from_user.username
        if message.from_user
        else "-",
    )

    # =====================================================
    # LOADING MESSAGE
    # =====================================================

    loading_message = None

    try:

        loading_message = await message.answer(
            "🧠 *XAU AI FUNDAMENTAL ANALYSIS*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "🔎 Sedang mencari berita terbaru...\n"
            "⏳ Mohon tunggu...",
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "Gagal mengirim loading message."
        )

    # =====================================================
    # FETCH FUNDAMENTAL
    # =====================================================

    try:

        news = await asyncio.to_thread(
            get_latest_fundamental_news
        )

    except Exception:

        logger.exception(
            "Gagal mengambil fundamental news."
        )

        news = None

    # =====================================================
    # NO NEWS
    # =====================================================

    if not news:

        text = (
            "📰 *FUNDAMENTAL GOLD*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Tidak ada berita fundamental valid "
            "yang tersedia saat ini.\n\n"
            "Kemungkinan penyebab:\n"
            "• Tidak ada berita baru\n"
            "• Berita sudah pernah diproses\n"
            "• Berita terlalu lama\n"
            "• Berita tidak relevan dengan Gold\n"
            "• News API sedang bermasalah\n\n"
            "📌 SMC tetap dapat digunakan "
            "seperti biasa."
        )

        try:

            if loading_message:

                await loading_message.edit_text(
                    text,
                    parse_mode="Markdown",
                )

            else:

                await message.answer(
                    text,
                    parse_mode="Markdown",
                )

        except Exception:

            logger.exception(
                "Gagal mengirim response "
                "fundamental kosong."
            )

        return

    # =====================================================
    # FORMAT NEWS
    # =====================================================

    try:

        text = format_fundamental_news(
            news
        )

    except Exception:

        logger.exception(
            "Gagal memformat fundamental news."
        )

        text = (
            "📰 *FUNDAMENTAL GOLD*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Berita berhasil ditemukan, "
            "tetapi gagal memformat hasil analisis."
        )

    # =====================================================
    # EXTRA ANALYSIS
    # =====================================================

    impact = str(
        news.get(
            "gold_impact",
            "NEUTRAL",
        )
        or "NEUTRAL"
    ).upper()

    age_minutes = news.get(
        "age_minutes"
    )

    score = news.get(
        "score"
    )

    # =====================================================
    # IMPACT EXPLANATION
    # =====================================================

    if impact == "BULLISH":

        impact_explanation = (
            "🟢 *Bias fundamental mendukung GOLD.*\n"
            "Tekanan fundamental saat ini cenderung "
            "mendukung kenaikan Gold."
        )

    elif impact == "BEARISH":

        impact_explanation = (
            "🔴 *Bias fundamental menekan GOLD.*\n"
            "Tekanan fundamental saat ini cenderung "
            "mendukung penurunan Gold."
        )

    else:

        impact_explanation = (
            "🟡 *Fundamental masih MIXED / NEUTRAL.*\n"
            "Belum terdapat dominasi fundamental "
            "yang cukup kuat ke satu arah."
        )

    # =====================================================
    # AGE TEXT
    # =====================================================

    age_text = ""

    if isinstance(
        age_minutes,
        (
            int,
            float,
        ),
    ):

        if age_minutes < 60:

            age_text = (
                f"⏱ Umur berita: "
                f"{age_minutes:.0f} menit"
            )

        else:

            age_hours = (
                age_minutes / 60
            )

            age_text = (
                f"⏱ Umur berita: "
                f"{age_hours:.1f} jam"
            )

    # =====================================================
    # SCORE TEXT
    # =====================================================

    score_text = ""

    if isinstance(
        score,
        (
            int,
            float,
        ),
    ):

        score_text = (
            f"⭐ News Score: "
            f"{int(score)}"
        )

    # =====================================================
    # ADD ANALYSIS
    # =====================================================

    extra_lines = [
        "",
        "━━━━━━━━━━━━━━━━━━",
        "",
        "🤖 *AI FUNDAMENTAL READ*",
        "",
        impact_explanation,
    ]

    if age_text:

        extra_lines.extend(
            [
                "",
                age_text,
            ]
        )

    if score_text:

        extra_lines.extend(
            [
                score_text,
            ]
        )

    extra_lines.extend(
        [
            "",
            "⚠️ *Catatan:*",
            "Fundamental digunakan sebagai "
            "layer tambahan untuk membaca kondisi "
            "makro Gold.",
            "",
            "📊 SMC tetap menjadi analisis utama "
            "untuk struktur dan entry.",
        ]
    )

    text = (
        text
        + "\n"
        + "\n".join(
            extra_lines
        )
    )

    # =====================================================
    # SEND / EDIT
    # =====================================================

    try:

        if loading_message:

            await loading_message.edit_text(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )

        else:

            await message.answer(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )

        logger.info(
            "Fundamental berhasil dikirim | "
            "impact=%s | "
            "score=%s",
            impact,
            score,
        )

    except Exception:

        logger.exception(
            "Gagal mengirim fundamental result."
        )

        # =================================================
        # FALLBACK
        # =================================================

        try:

            await message.answer(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=True,
            )

        except Exception:

            logger.exception(
                "Fallback fundamental juga gagal."
            )


# =========================================================
# OPTIONAL ALIAS
# =========================================================

@router.message(
    Command("news")
)
async def news_command(
    message: Message,
):
    """
    Alias:

        /news

    Dibuat sebagai shortcut menuju
    fundamental Gold.
    """

    await fundamental_command(
        message
    )
