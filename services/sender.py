"""
services/sender.py

Telegram Signal Sender (aiogram)
=================================

Fungsi:
- Mengirim signal ke member aktif
- Menyimpan signal short + detail
- Tombol Show / Hide Detail Analisa
- Tidak mengirim pesan baru ketika Detail diklik
- Retry Google Sheets
"""

import asyncio
import logging

from typing import Any, Dict

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from services.membership import get_active_members

from services.signal_builder import (
    TradeSignal,
    format_signal_short,
    format_signal_detail,
)

from services.signal_store import (
    save_signal,
)


logger = logging.getLogger(__name__)


# =====================================================
# CONFIG
# =====================================================

# Delay antar member.
# Sedikit lebih aman daripada 0.05 detik.
SEND_DELAY = 0.15

PARSE_MODE = "Markdown"


# =====================================================
# GOOGLE SHEETS RETRY
# =====================================================

MEMBER_RETRY_COUNT = 3
MEMBER_RETRY_DELAY = 2


# =====================================================
# FORMAT SIGNAL
# =====================================================

def format_trade_signal(signal) -> str:

    # =================================================
    # SUDAH STRING
    # =================================================

    if isinstance(
        signal,
        str
    ):

        return signal


    # =================================================
    # TradeSignal
    # =================================================

    if isinstance(
        signal,
        TradeSignal
    ):

        return format_signal_short(
            signal
        )


    # =================================================
    # OBJECT LAIN
    # =================================================

    try:

        return format_signal_short(
            signal
        )

    except Exception:

        logger.exception(
            "Object signal tidak dapat diformat."
        )

        raise


# =====================================================
# KEYBOARD DETAIL
# =====================================================

def create_detail_keyboard(
    signal_id: str,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Detail Analisa",
                    callback_data=(
                        f"detail:{signal_id}"
                    ),
                )
            ]
        ]
    )


# =====================================================
# GET ACTIVE MEMBERS WITH RETRY
# =====================================================

async def get_members_for_sending():

    for attempt in range(
        1,
        MEMBER_RETRY_COUNT + 1
    ):

        try:

            members = get_active_members()

            # ==========================================
            # GOOGLE SHEETS BERHASIL
            # ==========================================

            if members is not None:

                logger.info(
                    "Daftar member berhasil diambil | "
                    "attempt=%s | members=%s",
                    attempt,
                    len(members),
                )

                return members


            # ==========================================
            # GOOGLE SHEETS BELUM TERSEDIA
            # ==========================================

            logger.warning(
                "Google Sheets belum tersedia | "
                "attempt=%s/%s",
                attempt,
                MEMBER_RETRY_COUNT,
            )


        except Exception:

            logger.exception(
                "Error mengambil active members | "
                "attempt=%s/%s",
                attempt,
                MEMBER_RETRY_COUNT,
            )


        # ==============================================
        # RETRY
        # ==============================================

        if attempt < MEMBER_RETRY_COUNT:

            delay = (
                MEMBER_RETRY_DELAY
                * attempt
            )

            logger.info(
                "Retry mengambil member dalam %s detik...",
                delay,
            )

            await asyncio.sleep(
                delay
            )


    # =================================================
    # SEMUA RETRY GAGAL
    # =================================================

    logger.error(
        "Gagal mengambil daftar member setelah %s percobaan.",
        MEMBER_RETRY_COUNT,
    )

    return None


# =====================================================
# SEND SIGNAL TO MEMBERS
# =====================================================

async def send_signal_to_members(
    bot,
    signal_text,
) -> Dict[str, Any]:

    # =================================================
    # CHECK BOT
    # =================================================

    if bot is None:

        logger.error(
            "Bot Telegram tidak tersedia."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =================================================
    # VARIABLE
    # =================================================

    reply_markup = None

    signal_id = None


    # =================================================
    # TRADE SIGNAL
    #
    # Simpan:
    #
    # signal short
    # +
    # detail analisa
    #
    # menggunakan ID yang sama.
    # =================================================

    if isinstance(
        signal_text,
        TradeSignal
    ):

        try:

            # ==========================================
            # FORMAT SIGNAL SHORT
            # ==========================================

            short_text = format_signal_short(
                signal_text
            )


            # ==========================================
            # FORMAT DETAIL
            # ==========================================

            detail_text = format_signal_detail(
                signal_text
            )


            # ==========================================
            # SAVE SHORT + DETAIL
            # ==========================================

            signal_id = save_signal(

                short_text,

                detail_text,

            )


            # ==========================================
            # CREATE BUTTON
            # ==========================================

            reply_markup = (
                create_detail_keyboard(
                    signal_id
                )
            )


            logger.info(
                "Signal detail disimpan | "
                "signal_id=%s",
                signal_id,
            )


        except Exception:

            logger.exception(
                "Gagal membuat Detail Analisa."
            )

            # ==========================================
            # DETAIL ERROR TIDAK BOLEH MENGGAGALKAN
            # SIGNAL UTAMA
            # ==========================================

            reply_markup = None


    # =================================================
    # FORMAT SIGNAL
    # =================================================

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


    # =================================================
    # VALIDASI SIGNAL
    # =================================================

    if not isinstance(
        signal_text,
        str
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


    # =================================================
    # SIGNAL KOSONG
    # =================================================

    if not signal_text.strip():

        logger.error(
            "Signal text kosong."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =================================================
    # AMBIL MEMBER AKTIF
    # =================================================

    members = await get_members_for_sending()


    # =================================================
    # GOOGLE SHEETS ERROR
    # =================================================

    if members is None:

        logger.error(
            "SIGNAL TIDAK DIKIRIM: "
            "Google Sheets tidak tersedia setelah retry."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
            "spreadsheet_error": True,
            "retry": True,
        }


    # =================================================
    # TIDAK ADA MEMBER
    # =================================================

    if not members:

        logger.warning(
            "Google Sheets berhasil dibaca, "
            "tetapi tidak ada member aktif."
        )

        return {
            "success": 0,
            "failed": 0,
            "total": 0,
        }


    # =================================================
    # TOTAL MEMBER
    # =================================================

    total = len(
        members
    )

    success = 0

    failed = 0


    # =================================================
    # LOG
    # =================================================

    logger.info(
        "Mulai mengirim signal ke %s member aktif.",
        total,
    )


    # =================================================
    # SEND TO EACH MEMBER
    # =================================================

    for member in members:

        # =============================================
        # GET TELEGRAM ID
        # =============================================

        telegram_id = member.get(
            "telegram_id"
        )


        # =============================================
        # TELEGRAM ID KOSONG
        # =============================================

        if not telegram_id:

            logger.warning(
                "Telegram ID kosong: %s",
                member,
            )

            failed += 1

            continue


        # =============================================
        # CONVERT TELEGRAM ID
        # =============================================

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


        # =============================================
        # SEND TELEGRAM
        # =============================================

        try:

            await bot.send_message(

                chat_id=telegram_id,

                text=signal_text,

                parse_mode=PARSE_MODE,

                disable_web_page_preview=True,

                reply_markup=reply_markup,

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


        # =============================================
        # DELAY ANTAR MEMBER
        # =============================================

        if SEND_DELAY > 0:

            await asyncio.sleep(
                SEND_DELAY
            )


    # =================================================
    # RESULT
    # =================================================

    result = {

        "success": success,

        "failed": failed,

        "total": total,

    }


    # =================================================
    # LOG RESULT
    # =================================================

    logger.info(
        "Pengiriman signal selesai | "
        "success=%s | failed=%s | total=%s",

        success,

        failed,

        total,
    )


    return result
