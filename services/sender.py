"""
Telegram Signal Sender

Fungsi:
- Mengambil seluruh member aktif
- Mengirim signal ke masing-masing member
- Menggunakan Telegram Bot instance dari scheduler
- Menggunakan Markdown karena format signal memakai:
    *bold*
    _italic_
    `code`
- Tidak bergantung pada TELEGRAM_CHAT_ID pribadi
"""

import asyncio
import logging
from typing import Any, Dict

from services.membership import get_active_members


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

# Jeda antar pengiriman untuk mengurangi kemungkinan
# Telegram flood limit ketika member cukup banyak.
SEND_DELAY = 0.05

# Parse mode sesuai format signal_builder / signal_generator
PARSE_MODE = "Markdown"


# =========================================================
# SEND SIGNAL TO MEMBERS
# =========================================================

async def send_signal_to_members(
    bot,
    signal_text: str,
) -> Dict[str, Any]:
    """
    Kirim signal ke seluruh member aktif.

    Parameters
    ----------
    bot:
        Instance aiogram Bot.

    signal_text:
        Text signal yang sudah diformat.

    Returns
    -------
    dict:
        {
            "success": jumlah berhasil,
            "failed": jumlah gagal,
            "total": jumlah member,
        }
    """

    # =====================================================
    # VALIDASI
    # =====================================================

    if bot is None:

        logger.error(
            "Bot Telegram tidak tersedia."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    if not signal_text:

        logger.error(
            "Signal text kosong."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =====================================================
    # AMBIL MEMBER AKTIF
    # =====================================================

    try:

        members = get_active_members()

    except Exception:

        logger.exception(
            "Gagal mengambil daftar member aktif."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    if not members:

        logger.warning(
            "Tidak ada member aktif."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    total = len(members)

    success = 0
    failed = 0


    logger.info(
        "Mulai mengirim signal ke %s member aktif.",
        total,
    )


    # =====================================================
    # LOOP MEMBER
    # =====================================================

    for member in members:

        telegram_id = member.get(
            "telegram_id"
        )


        # =================================================
        # TELEGRAM ID KOSONG
        # =================================================

        if not telegram_id:

            logger.warning(
                "Telegram ID kosong: %s",
                member,
            )

            failed += 1

            continue


        # =================================================
        # NORMALISASI TELEGRAM ID
        # =================================================

        try:

            telegram_id = int(
                telegram_id
            )

        except (
            ValueError,
            TypeError,
        ):

            logger.warning(
                "Telegram ID tidak valid: %s",
                telegram_id,
            )

            failed += 1

            continue


        # =================================================
        # KIRIM
        # =================================================

        try:

            await bot.send_message(

                chat_id=telegram_id,

                text=signal_text,

                parse_mode=PARSE_MODE,

                disable_web_page_preview=True,

            )


            success += 1


            logger.info(
                "Signal TERKIRIM → %s",
                telegram_id,
            )


        except Exception as e:

            failed += 1


            logger.error(
                "Signal GAGAL → %s | %s",
                telegram_id,
                e,
            )


        # =================================================
        # DELAY
        # =================================================

        if SEND_DELAY > 0:

            await asyncio.sleep(
                SEND_DELAY
            )


    # =====================================================
    # HASIL
    # =====================================================

    result = {

        "success": success,

        "failed": failed,

        "total": total,

    }


    logger.info(
        "Pengiriman signal selesai | "
        "success=%s | failed=%s | total=%s",
        success,
        failed,
        total,
    )


    return result
