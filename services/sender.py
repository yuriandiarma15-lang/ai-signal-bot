"""
services/sender.py

XAU AI SIGNAL BOT
=================

Telegram Signal Sender

Fungsi:
- Mengirim signal ke member aktif
- Mengirim signal yang sama ke Group Topic
- Menyimpan signal SHORT + DETAIL
- Satu signal menggunakan satu signal_id
- Tombol "📊 Detail Analisa" hanya untuk member pribadi
- Detail tidak dikirim sebagai pesan baru
- Retry Google Sheets
- Retry Telegram
- Validasi Telegram ID
- Tidak menghentikan broadcast jika satu member gagal
- Group Topic menggunakan signal yang sama dengan private

FLOW:

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
Private:
    short_text + Detail Keyboard

Group:
    short_text dipotong sampai RR
    + garis
    + footer XAU AI SMC REAL
    ↓
Group Topic
"""


# =========================================================
# IMPORT
# =========================================================

import asyncio
import logging
import os

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


# =========================================================
# LOGGER
# =========================================================

logger = logging.getLogger(
    __name__
)


# =========================================================
# CONFIG
# =========================================================

# ---------------------------------------------------------
# Delay antar member
# ---------------------------------------------------------

SEND_DELAY = 0.15


# ---------------------------------------------------------
# Parse mode
# ---------------------------------------------------------

PARSE_MODE = "Markdown"


# =========================================================
# GROUP CONFIG
# =========================================================

# ---------------------------------------------------------
# Telegram Group ID
#
# Contoh:
#
# GROUP_SIGNAL_CHAT_ID=-1001234567890
#
# ---------------------------------------------------------

GROUP_SIGNAL_CHAT_ID = os.getenv(
    "GROUP_SIGNAL_CHAT_ID",
    ""
).strip()


# ---------------------------------------------------------
# Telegram Topic ID
#
# Contoh:
#
# GROUP_SIGNAL_TOPIC_ID=123
#
# ---------------------------------------------------------

GROUP_SIGNAL_TOPIC_ID = os.getenv(
    "GROUP_SIGNAL_TOPIC_ID",
    ""
).strip()


# =========================================================
# GOOGLE SHEETS RETRY
# =========================================================

MEMBER_RETRY_COUNT = 3

MEMBER_RETRY_DELAY = 2


# =========================================================
# TELEGRAM RETRY
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

        # Group information
        "group_success": False,
        "group_failed": False,
        "group_chat_id": GROUP_SIGNAL_CHAT_ID,
        "group_topic_id": GROUP_SIGNAL_TOPIC_ID,

        # Signal
        "signal_id": None,
    }


# =========================================================
# FORMAT SIGNAL PRIVATE
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
# FORMAT SIGNAL GROUP
# =========================================================

def format_signal_group(
    short_text: str,
) -> str:
    """
    Membuat format signal khusus Group Topic.

    DATA TIDAK DIHITUNG ULANG.

    short_text berasal dari signal yang sama
    yang dikirim ke private member.

    Group hanya menampilkan sampai baris RR.

    Tidak menampilkan:
    - Low Risk Zone
    - Detail Analisa
    - tombol
    - disclaimer
    - money management

    Format akhir:

    🚨 XAU AI SMC REAL
    ━━━━━━━━━━━━━━━━━━
    ...
    📐 RR : ...
    ━━━━━━━━━━━━━━━━━━
    🤖 XAU AI SMC REAL — AI Agent Gold
    """

    if not isinstance(
        short_text,
        str,
    ):

        return ""


    if not short_text.strip():

        return ""


    lines = short_text.splitlines()

    group_lines = []


    # =====================================================
    # AMBIL SAMPAI RR
    # =====================================================

    found_rr = False

    for line in lines:

        # -------------------------------------------------
        # Jika sudah menemukan RR, jangan ambil baris
        # setelahnya.
        # -------------------------------------------------

        if found_rr:
            break


        group_lines.append(
            line
        )


        # -------------------------------------------------
        # Deteksi baris RR
        #
        # Contoh:
        #
        # 📐 RR  : TP1 1:1.10 | TP2 1:1.90
        #
        # -------------------------------------------------

        stripped = line.strip()

        if stripped.startswith(
            "📐 RR"
        ):

            found_rr = True


    # =====================================================
    # FALLBACK
    # =====================================================

    # Jika format signal tidak memiliki baris RR,
    # gunakan seluruh short_text.
    #
    # Ini mencegah group_text menjadi kosong.

    if not found_rr:

        group_lines = lines


    # =====================================================
    # HAPUS KOSONG DI AKHIR
    # =====================================================

    while group_lines and not group_lines[-1].strip():

        group_lines.pop()


    # =====================================================
    # GARIS PEMBATAS
    # =====================================================

    group_lines.append(
        "━━━━━━━━━━━━━━━━━━"
    )


    # =====================================================
    # FOOTER GROUP
    # =====================================================

    group_lines.append(
        "🤖 XAU AI SMC REAL — AI Agent Gold"
    )


    # =====================================================
    # RESULT
    # =====================================================

    return "\n".join(
        group_lines
    )


# =========================================================
# DETAIL KEYBOARD
# =========================================================

def create_detail_keyboard(
    signal_id: str,
) -> InlineKeyboardMarkup:

    """
    Membuat tombol Detail Analisa.

    Tombol hanya digunakan untuk private member.

    callback_data:
        detail:<signal_id>
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
    message_thread_id: Optional[int] = None,
) -> bool:

    """
    Mengirim satu pesan Telegram.

    Bisa digunakan untuk:
    - Private
    - Group Topic

    Retry hanya untuk error sementara.
    """

    for attempt in range(
        1,
        TELEGRAM_RETRY_COUNT + 1,
    ):

        try:

            send_kwargs = {
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": PARSE_MODE,
                "disable_web_page_preview": True,
                "reply_markup": reply_markup,
            }


            # =================================================
            # TOPIC
            # =================================================

            if message_thread_id is not None:

                send_kwargs[
                    "message_thread_id"
                ] = message_thread_id


            await bot.send_message(
                **send_kwargs
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
                "topic=%s | "
                "retry_after=%s | "
                "attempt=%s/%s",
                telegram_id,
                message_thread_id,
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
                "topic=%s | "
                "attempt=%s/%s | error=%s",
                telegram_id,
                message_thread_id,
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
                "topic=%s | "
                "attempt=%s/%s | error=%s",
                telegram_id,
                message_thread_id,
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
        # USER BLOCKED BOT / FORBIDDEN
        # =================================================

        except TelegramForbiddenError as e:

            logger.warning(
                "Telegram Forbidden | "
                "telegram_id=%s | "
                "topic=%s | error=%s",
                telegram_id,
                message_thread_id,
                repr(e),
            )

            return False


        # =================================================
        # BAD REQUEST
        # =================================================

        except TelegramBadRequest as e:

            logger.error(
                "Telegram BadRequest | "
                "telegram_id=%s | "
                "topic=%s | error=%s",
                telegram_id,
                message_thread_id,
                repr(e),
            )

            return False


        # =================================================
        # ERROR LAIN
        # =================================================

        except Exception as e:

            logger.exception(
                "Error tidak terduga saat mengirim Telegram | "
                "telegram_id=%s | "
                "topic=%s | "
                "attempt=%s/%s",
                telegram_id,
                message_thread_id,
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
# SEND SIGNAL TO GROUP TOPIC
# =========================================================

async def send_signal_to_group(
    bot,
    group_text: str,
) -> bool:

    """
    Mengirim signal ke Telegram Group Topic.

    Tidak menggunakan tombol Detail.

    Tidak membuat signal baru.

    group_text berasal dari TradeSignal yang sama
    dengan private member.
    """

    # =====================================================
    # CHECK GROUP ID
    # =====================================================

    if not GROUP_SIGNAL_CHAT_ID:

        logger.warning(
            "GROUP_SIGNAL_CHAT_ID belum dikonfigurasi. "
            "Signal group dilewati."
        )

        return False


    # =====================================================
    # CHECK TOPIC ID
    # =====================================================

    if not GROUP_SIGNAL_TOPIC_ID:

        logger.warning(
            "GROUP_SIGNAL_TOPIC_ID belum dikonfigurasi. "
            "Signal group dilewati."
        )

        return False


    # =====================================================
    # VALIDATE GROUP ID
    # =====================================================

    try:

        group_chat_id = int(
            GROUP_SIGNAL_CHAT_ID
        )

    except (
        ValueError,
        TypeError,
    ):

        logger.error(
            "GROUP_SIGNAL_CHAT_ID tidak valid: %s",
            GROUP_SIGNAL_CHAT_ID,
        )

        return False


    # =====================================================
    # VALIDATE TOPIC ID
    # =====================================================

    try:

        topic_id = int(
            GROUP_SIGNAL_TOPIC_ID
        )

    except (
        ValueError,
        TypeError,
    ):

        logger.error(
            "GROUP_SIGNAL_TOPIC_ID tidak valid: %s",
            GROUP_SIGNAL_TOPIC_ID,
        )

        return False


    # =====================================================
    # VALIDATE TEXT
    # =====================================================

    if not group_text:

        logger.error(
            "Group signal text kosong."
        )

        return False


    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "Mengirim signal ke Group Topic | "
        "chat_id=%s | topic_id=%s",
        group_chat_id,
        topic_id,
    )


    # =====================================================
    # SEND
    # =====================================================

    sent = await send_one_message(
        bot=bot,
        telegram_id=group_chat_id,
        text=group_text,
        reply_markup=None,
        message_thread_id=topic_id,
    )


    # =====================================================
    # RESULT
    # =====================================================

    if sent:

        logger.info(
            "=========================================="
        )

        logger.info(
            "GROUP SIGNAL TERKIRIM"
        )

        logger.info(
            "Group ID : %s",
            group_chat_id,
        )

        logger.info(
            "Topic ID : %s",
            topic_id,
        )

        logger.info(
            "=========================================="
        )

    else:

        logger.error(
            "GROUP SIGNAL GAGAL | "
            "chat_id=%s | topic_id=%s",
            group_chat_id,
            topic_id,
        )


    return sent


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
    Mengirim SATU signal yang sama ke:

    1. Member pribadi
    2. Group Topic

    Private:
        short_text
        + Detail Analisa button

    Group:
        signal-only
        sampai RR
        + footer

    Return:

    {
        "success": int,
        "failed": int,
        "total": int,
        "signal_id": str | None,
        "group_success": bool,
        "group_failed": bool
    }
    """

    # =====================================================
    # CHECK BOT
    # =====================================================

    if bot is None:

        logger.error(
            "Bot Telegram tidak tersedia."
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
            "Gagal mempersiapkan signal."
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
            "Signal text kosong."
        )

        return empty_result()


    # =====================================================
    # PREPARE GROUP SIGNAL
    # =====================================================

    group_text = format_signal_group(
        short_text
    )


    if not group_text:

        logger.warning(
            "Group signal text kosong."
        )


    # =====================================================
    # RESULT
    # =====================================================

    result = empty_result()


    result[
        "signal_id"
    ] = signal_id


    # =====================================================
    # SEND TO GROUP FIRST
    #
    # Penting:
    #
    # Group tidak bergantung pada Google Sheets.
    #
    # Jadi walaupun Sheets error,
    # signal tetap dicoba dikirim ke Group Topic.
    # =====================================================

    if group_text:

        try:

            group_sent = await send_signal_to_group(
                bot=bot,
                group_text=group_text,
            )


            result[
                "group_success"
            ] = group_sent


            result[
                "group_failed"
            ] = not group_sent


        except Exception:

            logger.exception(
                "Error mengirim signal ke Group Topic."
            )

            result[
                "group_success"
            ] = False

            result[
                "group_failed"
            ] = True


    # =====================================================
    # GET ACTIVE MEMBERS
    # =====================================================

    members = await get_members_for_sending()


    # =====================================================
    # GOOGLE SHEETS ERROR
    # =====================================================

    if members is None:

        logger.error(
            "SIGNAL MEMBER TIDAK DIKIRIM: "
            "Google Sheets tidak tersedia setelah retry."
        )


        result[
            "spreadsheet_error"
        ] = True


        result[
            "retry"
        ] = True


        return result


    # =====================================================
    # NO ACTIVE MEMBERS
    # =====================================================

    if not members:

        logger.warning(
            "Google Sheets berhasil dibaca, "
            "tetapi tidak ada member aktif."
        )


        return result


    # =====================================================
    # TOTAL
    # =====================================================

    total = len(
        members
    )

    success = 0

    failed = 0


    result[
        "total"
    ] = total


    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "=================================================="
    )

    logger.info(
        "Mulai broadcast signal ke member"
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
        "Group success: %s",
        result[
            "group_success"
        ],
    )

    logger.info(
        "=================================================="
    )


    # =====================================================
    # SEND LOOP MEMBER
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
        # SEND PRIVATE
        #
        # PRIVATE tetap mendapatkan tombol Detail.
        # =================================================

        sent = await send_one_message(

            bot=bot,

            telegram_id=telegram_id,

            text=short_text,

            reply_markup=reply_markup,

            message_thread_id=None,

        )


        # =================================================
        # RESULT
        # =================================================

        if sent:

            success += 1

            logger.info(
                "Signal PRIVATE TERKIRIM | "
                "[%s/%s] | telegram_id=%s",
                index,
                total,
                telegram_id,
            )

        else:

            failed += 1

            logger.error(
                "Signal PRIVATE GAGAL | "
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

    result[
        "success"
    ] = success


    result[
        "failed"
    ] = failed


    result[
        "total"
    ] = total


    result[
        "signal_id"
    ] = signal_id


    # =====================================================
    # FINAL LOG
    # =====================================================

    logger.info(
        "=================================================="
    )

    logger.info(
        "Pengiriman signal selesai"
    )

    logger.info(
        "Signal ID      : %s",
        signal_id,
    )

    logger.info(
        "Private Success: %s",
        success,
    )

    logger.info(
        "Private Failed : %s",
        failed,
    )

    logger.info(
        "Private Total  : %s",
        total,
    )

    logger.info(
        "Group Success  : %s",
        result[
            "group_success"
        ],
    )

    logger.info(
        "Group Failed   : %s",
        result[
            "group_failed"
        ],
    )

    logger.info(
        "Group Chat ID  : %s",
        GROUP_SIGNAL_CHAT_ID,
    )

    logger.info(
        "Group Topic ID : %s",
        GROUP_SIGNAL_TOPIC_ID,
    )

    logger.info(
        "=================================================="
    )


    return result
