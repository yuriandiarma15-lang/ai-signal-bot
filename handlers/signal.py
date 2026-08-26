from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.filters import Command

import asyncio
import logging

from config.settings import (
    SOURCE_GROUP_ID,
    ADMIN_USERNAME,
)

from services.membership import (
    get_active_members,
)

from services.scheduler import (
    trading_open,
)

from services.signal_builder import (
    generate_signal,
    format_signal_short,
    format_signal_detail,
    NoTradeSignal,
)

from services.signal_store import (
    save_signal,
    get_signal,
    get_detail,
)


router = Router()

logger = logging.getLogger(
    "signal_handler"
)


# =========================================================
# KEYBOARD - SHOW DETAIL
# =========================================================

def detail_keyboard(
    signal_id: str,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Detail Analisa",
                    callback_data=f"detail:{signal_id}",
                )
            ]
        ]
    )


# =========================================================
# KEYBOARD - HIDE DETAIL
# =========================================================

def hide_detail_keyboard(
    signal_id: str,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔽 Hide Detail",
                    callback_data=f"hide:{signal_id}",
                )
            ]
        ]
    )


# =========================================================
# ADMIN MANUAL SIGNAL
# =========================================================

@router.message(
    Command("signal")
)
async def manual_signal(
    message: Message,
):

    username = (
        message.from_user.username
        if message.from_user
        else None
    )

    # =====================================================
    # CHECK USERNAME
    # =====================================================

    if not username:

        await message.answer(
            "❌ Username Telegram tidak ditemukan."
        )

        return


    # =====================================================
    # CHECK ADMIN
    # =====================================================

    admin_username = (
        ADMIN_USERNAME
        .replace("@", "")
        .strip()
    )

    if username.lower() != admin_username.lower():

        await message.answer(
            "❌ Akses ditolak."
        )

        return


    # =====================================================
    # LOG
    # =====================================================

    logger.info(
        "ADMIN REQUEST SIGNAL | @%s",
        username,
    )


    # =====================================================
    # INFO PROCESSING
    # =====================================================

    await message.answer(

        "⏳ *Sedang menganalisa XAUUSD...*\n\n"
        "M5 → SMC Structure\n"
        "M1 → Entry Timing\n"
        "OB / FVG / Liquidity\n"
        "Risk Management",

        parse_mode="Markdown",

    )


    # =====================================================
    # GENERATE SIGNAL
    #
    # Manual:
    # 12 candle M5 CLOSED
    # =====================================================

    try:

        signal = await asyncio.to_thread(

            generate_signal,

            structure_candle_count=12,

        )

    except NoTradeSignal as e:

        logger.info(
            "ADMIN /signal -> NO TRADE | %s",
            e,
        )

        await message.answer(

            "⚠️ *NO TRADE*\n\n"
            f"{str(e)}",

            parse_mode="Markdown",

        )

        return

    except Exception:

        logger.exception(
            "ERROR GENERATE MANUAL SIGNAL"
        )

        await message.answer(

            "❌ *Gagal membuat signal.*\n\n"
            "Terjadi error pada engine analisa.\n"
            "Silakan coba kembali.",

            parse_mode="Markdown",

        )

        return


    # =====================================================
    # LOG HASIL
    # =====================================================

    logger.info(

        "MANUAL SIGNAL CREATED | "
        "bias=%s | "
        "entry=%s | "
        "order=%s | "
        "probability=%s%%",

        getattr(
            signal,
            "bias",
            "-",
        ),

        getattr(
            signal,
            "entry_price",
            "-",
        ),

        getattr(
            signal,
            "order_type",
            "-",
        ),

        getattr(
            signal,
            "probability",
            "-",
        ),

    )


    # =====================================================
    # FORMAT SIGNAL
    # =====================================================

    try:

        signal_text = format_signal_short(
            signal
        )

        detail_text = format_signal_detail(
            signal
        )

    except Exception:

        logger.exception(
            "ERROR FORMAT SIGNAL MESSAGE"
        )

        await message.answer(

            "❌ Signal berhasil dianalisa, "
            "tetapi gagal memformat pesan Telegram."

        )

        return


    # =====================================================
    # SIMPAN SIGNAL + DETAIL
    #
    # Keduanya menggunakan signal_id yang sama.
    #
    # signal_id
    # ├── signal_text
    # └── detail_text
    # =====================================================

    try:

        signal_id = save_signal(

            signal_text,

            detail_text,

        )

        logger.info(

            "SIGNAL STORE SAVED | "
            "signal_id=%s",

            signal_id,

        )

    except Exception:

        logger.exception(
            "ERROR SAVE SIGNAL + DETAIL"
        )

        signal_id = None


    # =====================================================
    # SIAPKAN TOMBOL
    # =====================================================

    reply_markup = None

    if signal_id:

        reply_markup = detail_keyboard(
            signal_id
        )


    # =====================================================
    # SEND SIGNAL
    # =====================================================

    try:

        await message.answer(

            signal_text,

            parse_mode="Markdown",

            reply_markup=reply_markup,

        )

        logger.info(
            "MANUAL SIGNAL BERHASIL DIKIRIM."
        )

    except Exception:

        logger.exception(
            "ERROR SEND MANUAL SIGNAL"
        )

        # =================================================
        # FALLBACK TANPA MARKDOWN
        # =================================================

        try:

            await message.answer(

                signal_text,

                reply_markup=reply_markup,

            )

        except Exception:

            logger.exception(
                "FALLBACK SEND SIGNAL JUGA GAGAL."
            )


# =========================================================
# SHOW DETAIL ANALISA
#
# PENTING:
# Tidak mengirim pesan baru.
#
# Pesan signal lama diedit menjadi detail.
# =========================================================

@router.callback_query(
    F.data.startswith("detail:")
)
async def handle_detail_callback(
    callback: CallbackQuery,
):

    # =====================================================
    # HENTIKAN LOADING BUTTON
    # =====================================================

    await callback.answer()


    # =====================================================
    # VALIDASI MESSAGE
    # =====================================================

    if not callback.message:

        logger.warning(
            "Callback detail tanpa message."
        )

        return


    # =====================================================
    # AMBIL SIGNAL ID
    # =====================================================

    signal_id = callback.data.split(
        ":",
        1,
    )[1]


    # =====================================================
    # AMBIL DETAIL
    # =====================================================

    detail_text = get_detail(
        signal_id
    )


    if detail_text is None:

        logger.warning(

            "Detail analisa tidak ditemukan | "
            "signal_id=%s",

            signal_id,

        )

        await callback.answer(

            "⚠️ Detail analisa sudah kadaluarsa.",

            show_alert=True,

        )

        return


    # =====================================================
    # EDIT PESAN YANG SAMA
    # =====================================================

    try:

        await callback.message.edit_text(

            detail_text,

            parse_mode="Markdown",

            reply_markup=hide_detail_keyboard(
                signal_id
            ),

        )

        logger.info(

            "DETAIL ANALISA SHOW | "
            "signal_id=%s",

            signal_id,

        )

    except Exception:

        logger.exception(
            "ERROR SHOW DETAIL ANALISA"
        )

        # =================================================
        # FALLBACK TANPA MARKDOWN
        # =================================================

        try:

            await callback.message.edit_text(

                detail_text,

                reply_markup=hide_detail_keyboard(
                    signal_id
                ),

            )

        except Exception:

            logger.exception(
                "FALLBACK SHOW DETAIL GAGAL."
            )


# =========================================================
# HIDE DETAIL ANALISA
#
# PENTING:
# Tidak mengirim pesan baru.
#
# Pesan detail lama dikembalikan menjadi
# signal short/original.
# =========================================================

@router.callback_query(
    F.data.startswith("hide:")
)
async def handle_hide_callback(
    callback: CallbackQuery,
):

    # =====================================================
    # HENTIKAN LOADING BUTTON
    # =====================================================

    await callback.answer()


    # =====================================================
    # VALIDASI MESSAGE
    # =====================================================

    if not callback.message:

        logger.warning(
            "Callback hide tanpa message."
        )

        return


    # =====================================================
    # AMBIL SIGNAL ID
    # =====================================================

    signal_id = callback.data.split(
        ":",
        1,
    )[1]


    # =====================================================
    # AMBIL SIGNAL ORIGINAL
    # =====================================================

    signal_text = get_signal(
        signal_id
    )


    if signal_text is None:

        logger.warning(

            "Signal short tidak ditemukan | "
            "signal_id=%s",

            signal_id,

        )

        await callback.answer(

            "⚠️ Signal utama sudah kadaluarsa.",

            show_alert=True,

        )

        return


    # =====================================================
    # EDIT PESAN YANG SAMA
    # =====================================================

    try:

        await callback.message.edit_text(

            signal_text,

            parse_mode="Markdown",

            reply_markup=detail_keyboard(
                signal_id
            ),

        )

        logger.info(

            "DETAIL ANALISA HIDE | "
            "signal_id=%s",

            signal_id,

        )

    except Exception:

        logger.exception(
            "ERROR HIDE DETAIL ANALISA"
        )

        # =================================================
        # FALLBACK TANPA MARKDOWN
        # =================================================

        try:

            await callback.message.edit_text(

                signal_text,

                reply_markup=detail_keyboard(
                    signal_id
                ),

            )

        except Exception:

            logger.exception(
                "FALLBACK HIDE DETAIL GAGAL."
            )


# =========================================================
# RECEIVE SIGNAL FROM OLD SOURCE GROUP
#
# Catatan:
# Jalur ini menerima text biasa dari source group.
#
# Karena source group hanya memberikan text,
# sistem Detail Analisa tidak dibuat di jalur ini.
# =========================================================

@router.message(
    F.chat.id == SOURCE_GROUP_ID
)
async def receive_signal(
    message: Message,
):

    print(
        "\n======================"
    )

    print(
        "=== SIGNAL GROUP MASUK ==="
    )

    print(
        "======================"
    )


    # =====================================================
    # TRADING SESSION CHECK
    # =====================================================

    if not trading_open():

        print(
            "DILUAR JAM TRADING"
        )

        return


    # =====================================================
    # CHECK TEXT
    # =====================================================

    if not message.text:

        print(
            "TEXT KOSONG"
        )

        return


    # =====================================================
    # GET SIGNAL
    # =====================================================

    signal_text = message.text


    print(
        "SIGNAL DITERUSKAN:"
    )

    print(
        signal_text
    )


    # =====================================================
    # GET ACTIVE MEMBERS
    # =====================================================

    try:

        members = get_active_members()

    except Exception:

        logger.exception(
            "Gagal mengambil active members."
        )

        return


    if not members:

        print(
            "TIDAK ADA MEMBER AKTIF"
        )

        return


    print(
        "TOTAL MEMBER:",
        len(members),
    )


    # =====================================================
    # SEND TO MEMBERS
    # =====================================================

    for member in members:

        telegram_id = member.get(
            "telegram_id"
        )


        if not telegram_id:

            continue


        try:

            await message.bot.send_message(

                chat_id=int(
                    telegram_id
                ),

                text=signal_text,

            )

            print(
                "TERKIRIM:",
                telegram_id
            )


        except Exception as e:

            print(
                "GAGAL:",
                telegram_id,
                e
            )
