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
    save_detail,
    get_detail,
)


router = Router()

logger = logging.getLogger(
    "signal_handler"
)


# =========================================================
# ADMIN MANUAL SIGNAL
# =========================================================

@router.message(
    Command("signal")
)
async def manual_signal(
    message: Message
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
    # Manual /signal:
    # menggunakan 12 candle M5 CLOSED
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
        getattr(signal, "bias", "-"),
        getattr(signal, "entry_price", "-"),
        getattr(signal, "order_type", "-"),
        getattr(signal, "probability", "-"),
    )

    # =====================================================
    # FORMAT TradeSignal -> TEXT SHORT + DETAIL
    # =====================================================

    try:

        signal_text = format_signal_short(signal)
        detail_text = format_signal_detail(signal)

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
    # SIMPAN DETAIL + SIAPKAN TOMBOL
    # =====================================================

    signal_id = save_detail(detail_text)

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Detail Analisa",
                    callback_data=f"detail:{signal_id}",
                )
            ]
        ]
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
        # FALLBACK TANPA MARKDOWN & TOMBOL
        # =================================================

        try:

            await message.answer(
                signal_text,
            )

        except Exception:

            logger.exception(
                "FALLBACK SEND SIGNAL JUGA GAGAL."
            )


# =========================================================
# TOMBOL "DETAIL ANALISA"
# =========================================================

@router.callback_query(
    F.data.startswith("detail:")
)
async def handle_detail_callback(
    callback: CallbackQuery
):

    await callback.answer()  # wajib, biar tombol tidak "loading" terus

    signal_id = callback.data.split(":", 1)[1]

    detail_text = get_detail(signal_id)

    if detail_text is None:

        await callback.message.answer(
            "⚠️ Detail analisa sudah kadaluarsa atau tidak ditemukan."
        )

        return

    try:

        await callback.message.answer(
            detail_text,
            parse_mode="Markdown",
        )

    except Exception:

        logger.exception(
            "ERROR SEND DETAIL ANALISA"
        )

        try:

            await callback.message.answer(
                detail_text,
            )

        except Exception:

            logger.exception(
                "FALLBACK SEND DETAIL JUGA GAGAL."
            )


# =========================================================
# RECEIVE SIGNAL FROM OLD SOURCE GROUP
# =========================================================

@router.message(
    F.chat.id == SOURCE_GROUP_ID
)
async def receive_signal(
    message: Message
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

    members = get_active_members()

    print(
        "TOTAL MEMBER:",
        len(members)
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

                text=signal_text

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
