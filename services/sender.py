"""
services/sender.py

Telegram Signal Sender
======================

Fungsi:
- Mengambil seluruh member aktif
- Mengirim signal ke masing-masing member
- Menerima:
    1. TradeSignal object
    2. string
- Jika TradeSignal:
    -> gunakan format_signal_message()
      dari signal_builder.py

PENTING:
Jangan melakukan formatting ulang di sini.
Format Telegram dikontrol oleh signal_builder.py.
"""

import asyncio
import logging

from typing import Any, Dict


from services.membership import (
    get_active_members,
)

from services.signal_builder import (
    TradeSignal,
    format_signal_message,
)


# =========================================================
# LOGGING
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# CONFIG
# =========================================================

SEND_DELAY = 0.05

PARSE_MODE = "Markdown"


# =========================================================
# FORMAT SIGNAL
# =========================================================

def format_trade_signal(
    signal
) -> str:
    """
    Compatibility wrapper.

    TradeSignal:
        menggunakan format_signal_message()

    String:
        langsung digunakan.
    """

    # -----------------------------------------------------
    # STRING
    # -----------------------------------------------------

    if isinstance(
        signal,
        str,
    ):

        return signal


    # -----------------------------------------------------
    # TRADE SIGNAL
    # -----------------------------------------------------

    if isinstance(
        signal,
        TradeSignal,
    ):

        return format_signal_message(
            signal
        )


    # -----------------------------------------------------
    # OBJECT YANG MIRIP TRADE SIGNAL
    # -----------------------------------------------------

    try:

        return format_signal_message(
            signal
        )

    except Exception:

        logger.exception(
            "Object signal tidak dapat diformat."
        )

        raise


# =========================================================
# SEND SIGNAL TO MEMBERS
# =========================================================

async def send_signal_to_members(
    bot,
    signal_text,
) -> Dict[str, Any]:

    """
    Kirim signal ke seluruh member aktif.

    signal_text boleh berupa:

    - str
    - TradeSignal object

    Jika TradeSignal object:
        otomatis menggunakan format_signal_message()
        dari services.signal_builder.
    """

    # =====================================================
    # VALIDASI BOT
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


    # =====================================================
    # CONVERT SIGNAL
    # =====================================================

    try:

        signal_text = format_trade_signal(
            signal_text
        )

    except Exception:

        logger.exception(
            "Gagal memformat signal."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =====================================================
    # VALIDASI STRING
    # =====================================================

    if not isinstance(
        signal_text,
        str,
    ):

        logger.error(
            "Signal bukan string: %s",
            type(signal_text),
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    if not signal_text.strip():

        logger.error(
            "Signal text kosong."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =====================================================
    # MEMBER AKTIF
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


    total = len(
        members
    )

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
        # ID KOSONG
        # =================================================

        if not telegram_id:

            logger.warning(
                "Telegram ID kosong: %s",
                member,
            )

            failed += 1

            continue


        # =================================================
        # NORMALISASI ID
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
        # SEND
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
                repr(e),
            )


        # =================================================
        # DELAY
        # =================================================

        if SEND_DELAY > 0:

            await asyncio.sleep(
                SEND_DELAY
            )


    # =====================================================
    # RESULT
    # =====================================================

    result = {

        "success":
            success,

        "failed":
            failed,

        "total":
            total,

    }


    logger.info(

        "Pengiriman signal selesai | "
        "success=%s | failed=%s | total=%s",

        success,

        failed,

        total,

    )


    return result
