"""
services/sender.py

XAU AI SIGNAL BOT
Telegram Signal Sender
=====================

Fungsi:
- Mengirim signal ke member aktif
- Menyimpan signal SHORT + DETAIL
- Satu signal menggunakan satu signal_id
- Tombol "📊 Detail Analisa"
- Detail tidak dikirim sebagai pesan baru
- Retry Google Sheets
- Retry Telegram
- Validasi Telegram ID
- Tidak menghentikan broadcast jika satu member gagal

FLOW
----

TradeSignal
    ↓
format_signal_short()
    ↓
format_signal_detail()
    ↓
save_signal(short, detail)
    ↓
signal_id
    ↓
create_detail_keyboard(signal_id)
    ↓
ambil member aktif
    ↓
kirim ke setiap member


CATATAN
-------

Callback tombol Detail ditangani oleh callback handler,
BUKAN oleh file ini.

Contoh callback_data:

    detail:ABC123

Callback handler nantinya mengambil signal berdasarkan
signal_id tersebut dan menampilkan detail menggunakan
edit_text / edit_caption sehingga tidak membuat pesan baru.
"""

import asyncio
import logging

from typing import Any, Dict, Optional


from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)


from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


from services.membership import (
    get_active_members,
)


from services.signal_builder import (
    TradeSignal,
    format_signal_short,
    format_signal_detail,
)


from services.signal_store import (
    save_signal,
)

from services.combined_signal import (
    process_signal,
)


logger = logging.getLogger(__name__)


# =========================================================
# CONFIG
# =========================================================

# Delay antar member.
#
# Tujuan:
# mengurangi risiko Telegram flood limit.
#
SEND_DELAY = 0.15


# Parse mode signal.
#
# Signal builder saat ini menggunakan Markdown.
#
PARSE_MODE = "Markdown"


# =========================================================
# GOOGLE SHEETS RETRY
# =========================================================

MEMBER_RETRY_COUNT = 3

MEMBER_RETRY_DELAY = 2


# =========================================================
# TELEGRAM RETRY
# =========================================================
#
# Retry hanya untuk error sementara.
#
# Jangan retry:
#
# - Forbidden
# - Chat tidak ditemukan
# - BadRequest permanen
#
# =========================================================

TELEGRAM_RETRY_COUNT = 3

TELEGRAM_RETRY_DELAY = 2


# =========================================================
# RESULT HELPER
# =========================================================

def empty_result(
    spreadsheet_error: bool = False,
    retry: bool = False,
) -> Dict[str, Any]:

    return {
        "success": 0,
        "failed": 0,
        "total": 0,
        "spreadsheet_error": spreadsheet_error,
        "retry": retry,
    }


# =========================================================
# FORMAT SIGNAL
# =========================================================

def format_trade_signal(
    signal,
) -> str:

    # =====================================================
    # STRING
    # =====================================================

    if isinstance(
        signal,
        str,
    ):

        return signal


    # =====================================================
    # TradeSignal
    # =====================================================

    if isinstance(
        signal,
        TradeSignal,
    ):

        return format_signal_short(
            signal,
        )


    # =====================================================
    # OBJECT LAIN
    # =====================================================

    try:

        return format_signal_short(
            signal,
        )

    except Exception:

        logger.exception(
            "Object signal tidak dapat diformat.",
        )

        raise


# =========================================================
# DETAIL KEYBOARD
# =========================================================

def create_detail_keyboard(
    signal_id: str,
) -> InlineKeyboardMarkup:

    """
    Membuat tombol Detail Analisa.

    callback_data:
        detail:<signal_id>

    Detail nantinya ditangani callback handler.
    """

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


# =========================================================
# VALIDATE TELEGRAM ID
# =========================================================

def normalize_telegram_id(
    telegram_id,
) -> Optional[int]:

    """
    Mengubah Telegram ID menjadi integer.

    Return:
        int  -> valid
        None -> invalid
    """

    if telegram_id is None:

        return None


    try:

        telegram_id = int(
            telegram_id
        )

    except (
        ValueError,
        TypeError,
    ):

        return None


    if telegram_id == 0:

        return None


    return telegram_id


# =========================================================
# GET ACTIVE MEMBERS
# =========================================================

async def get_members_for_sending():

    """
    Mengambil member aktif dari Google Sheets.

    Retry:
        3x

    Return:
        list -> berhasil
        None -> semua retry gagal
    """

    for attempt in range(
        1,
        MEMBER_RETRY_COUNT + 1,
    ):

        try:

            members = get_active_members()


            # =============================================
            # GOOGLE SHEETS BERHASIL
            # =============================================

            if members is not None:

                logger.info(
                    "Daftar member berhasil diambil | "
                    "attempt=%s | members=%s",
                    attempt,
                    len(members),
                )

                return members


            # =============================================
            # GOOGLE SHEETS BELUM TERSEDIA
            # =============================================

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


    # =====================================================
    # SEMUA RETRY GAGAL
    # =====================================================

    logger.error(
        "Gagal mengambil daftar member setelah %s percobaan.",
        MEMBER_RETRY_COUNT,
    )

    return None


# =========================================================
# SEND ONE TELEGRAM MESSAGE
# =========================================================

async def send_one_message(
    bot,
    telegram_id: int,
    text: str,
    reply_markup=None,
) -> bool:

    """
    Mengirim satu pesan Telegram.

    Retry hanya untuk error sementara.
    """

    for attempt in range(
        1,
        TELEGRAM_RETRY_COUNT + 1,
    ):

        try:

            await bot.send_message(

                chat_id=telegram_id,

                text=text,

                parse_mode=PARSE_MODE,

                disable_web_page_preview=True,

                reply_markup=reply_markup,

            )


            return True


        # =================================================
        # FLOOD CONTROL
        # =================================================

        except TelegramRetryAfter as e:

            retry_after = getattr(
                e,
                "retry_after",
                TELEGRAM_RETRY_DELAY,
            )


            logger.warning(
                "Telegram rate limit | "
                "telegram_id=%s | "
                "retry_after=%s | "
                "attempt=%s/%s",
                telegram_id,
                retry_after,
                attempt,
                TELEGRAM_RETRY_COUNT,
            )


            if attempt < TELEGRAM_RETRY_COUNT:

                await asyncio.sleep(
                    retry_after
                )


        # =================================================
        # TELEGRAM SERVER ERROR
        # =================================================

        except TelegramServerError as e:

            logger.warning(
                "Telegram server error | "
                "telegram_id=%s | "
                "attempt=%s/%s | error=%s",
                telegram_id,
                attempt,
                TELEGRAM_RETRY_COUNT,
                repr(e),
            )


            if attempt < TELEGRAM_RETRY_COUNT:

                await asyncio.sleep(
                    TELEGRAM_RETRY_DELAY
                    * attempt
                )


        # =================================================
        # NETWORK ERROR
        # =================================================

        except TelegramNetworkError as e:

            logger.warning(
                "Telegram network error | "
                "telegram_id=%s | "
                "attempt=%s/%s | error=%s",
                telegram_id,
                attempt,
                TELEGRAM_RETRY_COUNT,
                repr(e),
            )


            if attempt < TELEGRAM_RETRY_COUNT:

                await asyncio.sleep(
                    TELEGRAM_RETRY_DELAY
                    * attempt
                )


        # =================================================
        # USER BLOCKED BOT
        # =================================================

        except TelegramForbiddenError as e:

            logger.warning(
                "Telegram Forbidden | "
                "user mungkin memblokir bot | "
                "telegram_id=%s | error=%s",
                telegram_id,
                repr(e),
            )

            return False


        # =================================================
        # BAD REQUEST
        # =================================================

        except TelegramBadRequest as e:

            logger.error(
                "Telegram BadRequest | "
                "telegram_id=%s | error=%s",
                telegram_id,
                repr(e),
            )

            return False


        # =================================================
        # ERROR LAIN
        # =================================================

        except Exception as e:

            logger.exception(
                "Error tidak terduga saat mengirim Telegram | "
                "telegram_id=%s | attempt=%s/%s",
                telegram_id,
                attempt,
                TELEGRAM_RETRY_COUNT,
            )


            if attempt < TELEGRAM_RETRY_COUNT:

                await asyncio.sleep(
                    TELEGRAM_RETRY_DELAY
                    * attempt
                )


    return False


# =========================================================
# BUILD SIGNAL DATA
# =========================================================

def prepare_signal(
    signal,
):

    """
    Menyiapkan:

        short_text
        detail_text
        signal_id
        reply_markup

    Return:

        short_text,
        detail_text,
        signal_id,
        reply_markup
    """

    short_text = None

    detail_text = None

    signal_id = None

    reply_markup = None


    # =====================================================
    # TradeSignal
    # =====================================================

    if isinstance(
        signal,
        TradeSignal,
    ):

        # =================================================
        # SHORT
        # =================================================

        short_text = format_signal_short(
            signal,
        )


        # =================================================
        # DETAIL
        # =================================================

        detail_text = format_signal_detail(
            signal,
        )


        # =================================================
        # SAVE
        # =================================================

        signal_id = save_signal(

            short_text,

            detail_text,

        )


        # =================================================
        # VALIDATE SIGNAL ID
        # =================================================

        if signal_id:

            reply_markup = (
                create_detail_keyboard(
                    str(signal_id)
                )
            )


        logger.info(
            "Signal berhasil dipersiapkan | "
            "signal_id=%s",
            signal_id,
        )


        return (
            short_text,
            detail_text,
            signal_id,
            reply_markup,
        )


    # =====================================================
    # STRING / OBJECT
    # =====================================================

    short_text = format_trade_signal(
        signal,
    )


    return (
        short_text,
        None,
        None,
        None,
    )


# =========================================================
# SEND SIGNAL TO MEMBERS
# =========================================================

async def send_signal_to_members(
    bot,
    signal_text,
) -> Dict[str, Any]:

    """
    Mengirim signal ke seluruh member aktif.

    Return:

    {
        "success": int,
        "failed": int,
        "total": int,
        "signal_id": str | None
    }
    """

    # =====================================================
    # CHECK BOT
    # =====================================================

    if bot is None:

        logger.error(
            "Bot Telegram tidak tersedia.",
        )

        return empty_result()


    # =====================================================
    # PREPARE SIGNAL
    # =====================================================

    try:

        (
            short_text,
            detail_text,
            signal_id,
            reply_markup,
        ) = prepare_signal(
            signal_text
        )


    except Exception:

        logger.exception(
            "Gagal mempersiapkan signal.",
        )

        return empty_result()


    # =====================================================
    # VALIDATE TEXT
    # =====================================================

    if not isinstance(
        short_text,
        str,
    ):

        logger.error(
            "Signal bukan string: %s",
            type(short_text),
        )

        return empty_result()


    # =====================================================
    # EMPTY SIGNAL
    # =====================================================

    if not short_text.strip():

        logger.error(
            "Signal text kosong.",
        )

        return empty_result()


    # =====================================================
    # GET ACTIVE MEMBERS
    # =====================================================

    members = await get_members_for_sending()


    # =====================================================
    # GOOGLE SHEETS ERROR
    # =====================================================

    if members is None:

        logger.error(
            "SIGNAL TIDAK DIKIRIM: "
            "Google Sheets tidak tersedia setelah retry.",
        )

        result = empty_result(
            spreadsheet_error=True,
            retry=True,
        )

        if signal_id:

            result["signal_id"] = signal_id


        return result


    # =====================================================
    # NO ACTIVE MEMBERS
    # =====================================================

    if not members:

        logger.warning(
            "Google Sheets berhasil dibaca, "
            "tetapi tidak ada member aktif.",
        )

        result = empty_result()


        if signal_id:

            result["signal_id"] = signal_id


        return result


    # =====================================================
    # TOTAL
    # =====================================================

    total = len(
        members
    )

    success = 0

    failed = 0


    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "==================================================",
    )

    logger.info(
        "Mulai broadcast signal",
    )

    logger.info(
        "Total member : %s",
        total,
    )

    logger.info(
        "Signal ID    : %s",
        signal_id,
    )

    logger.info(
        "==================================================",
    )


    # =====================================================
    # SEND LOOP
    # =====================================================

    for index, member in enumerate(
        members,
        start=1,
    ):

        # =================================================
        # VALIDATE MEMBER OBJECT
        # =================================================

        if not isinstance(
            member,
            dict,
        ):

            logger.warning(
                "Data member tidak valid | "
                "index=%s | member=%r",
                index,
                member,
            )

            failed += 1

            continue


        # =================================================
        # TELEGRAM ID
        # =================================================

        raw_telegram_id = member.get(
            "telegram_id"
        )


        telegram_id = normalize_telegram_id(
            raw_telegram_id
        )


        # =================================================
        # INVALID TELEGRAM ID
        # =================================================

        if telegram_id is None:

            logger.warning(
                "Telegram ID tidak valid | "
                "index=%s | value=%r",
                index,
                raw_telegram_id,
            )

            failed += 1

            continue


        # =================================================
        # SEND
        # =================================================

        sent = await send_one_message(

            bot=bot,

            telegram_id=telegram_id,

            text=short_text,

            reply_markup=reply_markup,

        )


        # =================================================
        # RESULT
        # =================================================

        if sent:

            success += 1

            logger.info(
                "Signal TERKIRIM | "
                "[%s/%s] | telegram_id=%s",
                index,
                total,
                telegram_id,
            )

        else:

            failed += 1

            logger.error(
                "Signal GAGAL | "
                "[%s/%s] | telegram_id=%s",
                index,
                total,
                telegram_id,
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

        "success": success,

        "failed": failed,

        "total": total,

        "signal_id": signal_id,

    }


    # =====================================================
    # FINAL LOG
    # =====================================================

    logger.info(
        "==================================================",
    )

    logger.info(
        "Pengiriman signal selesai",
    )

    logger.info(
        "Signal ID : %s",
        signal_id,
    )

    logger.info(
        "Success    : %s",
        success,
    )

    logger.info(
        "Failed     : %s",
        failed,
    )

    logger.info(
        "Total      : %s",
        total,
    )

    logger.info(
        "==================================================",
    )


    return result
