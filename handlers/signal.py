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
from datetime import datetime
from zoneinfo import ZoneInfo

from config.settings import (
    SOURCE_GROUP_ID,
    ADMIN_USERNAME,
)

from services.membership import (
    get_active_members,
    check_member,
    get_manual_signal_limit,
)

from services.spreadsheet import (
    reserve_signal_request,
    refund_signal_request,
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
# REFUND MANUAL SIGNAL QUOTA
# =========================================================

async def refund_manual_quota(
    telegram_id: str,
    usage_date: str,
):
    """
    Mengembalikan kuota apabila proses manual signal gagal.
    """

    try:

        await asyncio.to_thread(
            refund_signal_request,
            telegram_id,
            usage_date,
        )

        logger.info(
            "MANUAL SIGNAL QUOTA REFUNDED | telegram_id=%s",
            telegram_id,
        )

    except Exception:

        logger.exception(
            "GAGAL REFUND MANUAL SIGNAL QUOTA | telegram_id=%s",
            telegram_id,
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

    if not message.from_user:
        return

    user = message.from_user

    username = user.username or ""

    telegram_id = str(user.id)

    # =====================================================
    # CHECK ADMIN
    # =====================================================

    admin_username = (
        (ADMIN_USERNAME or "")
        .replace("@", "")
        .strip()
    )

    is_admin = bool(
        admin_username
        and username
        and username.lower() == admin_username.lower()
    )

    # =====================================================
    # QUOTA CONFIG
    # =====================================================

    quota_reserved = False

    usage_date = datetime.now(
        ZoneInfo("Asia/Jakarta")
    ).strftime("%Y-%m-%d")

    daily_limit = 0

    used_count = 0

    package_name = ""

    # =====================================================
    # MEMBER VALIDATION
    # =====================================================

    if not is_admin:

        try:

            member = await asyncio.to_thread(
                check_member,
                telegram_id,
            )

        except Exception:

            logger.exception(
                "Gagal memeriksa membership."
            )

            await message.answer(
                "⚠️ Gagal memeriksa membership. "
                "Silakan coba kembali."
            )

            return

        # =================================================
        # SPREADSHEET ERROR
        # =================================================

        if member.get("error") == "spreadsheet_unavailable":

            await message.answer(
                "⚠️ Google Spreadsheet sedang tidak tersedia. "
                "Silakan coba kembali beberapa saat lagi."
            )

            return

        # =================================================
        # MEMBER NOT FOUND
        # =================================================

        if not member.get("found"):

            await message.answer(
                "🔒 Anda belum terdaftar sebagai member "
                "AI Assistants Gold."
            )

            return

        # =================================================
        # MEMBER EXPIRED
        # =================================================

        if not member.get("active"):

            await message.answer(
                "⛔ Langganan Anda sudah EXPIRED "
                "atau tidak aktif.\n\n"
                "Silakan lakukan aktivasi kembali."
            )

            return

        # =================================================
        # GET PACKAGE
        # =================================================

        package_name = (
            member.get("package")
            or member.get("paket")
            or member.get("broker")
            or "-"
        )

        # =================================================
        # GET DAILY LIMIT
        # =================================================

        daily_limit = get_manual_signal_limit(
            member
        )

        # =================================================
        # PACKAGE NOT ALLOWED
        # =================================================

        if daily_limit <= 0:

            await message.answer(
                "🔒 FITUR MANUAL SIGNAL\n\n"
                "Request manual signal hanya tersedia untuk:\n\n"
                "🥇 Paket 1 Tahun: 2 kali per hari\n"
                "💎 Paket 3 Tahun: 5 kali per hari\n\n"
                "Paket 1 Bulan dan 6 Bulan tidak "
                "mendapatkan akses request manual signal."
            )

            return

        # =================================================
        # RESERVE QUOTA
        # =================================================

        try:

            allowed, used_count = await asyncio.to_thread(
                reserve_signal_request,
                telegram_id,
                usage_date,
                daily_limit,
            )

        except Exception:

            logger.exception(
                "Gagal mencatat kuota manual signal."
            )

            await message.answer(
                "⚠️ Gagal memeriksa kuota request. "
                "Silakan coba kembali."
            )

            return

        # =================================================
        # QUOTA EXCEEDED
        # =================================================

        if not allowed:

            await message.answer(
                "⛔ KUOTA MANUAL SIGNAL HABIS\n\n"
                f"Paket: {package_name}\n"
                f"Pemakaian hari ini: "
                f"{used_count}/{daily_limit}\n\n"
                "Kuota direset setiap pukul 00.00 WIB."
            )

            return

        quota_reserved = True

    # =====================================================
    # LOG REQUEST
    # =====================================================

    logger.info(
        "MANUAL SIGNAL REQUEST | "
        "telegram_id=%s | username=@%s | admin=%s",
        telegram_id,
        username or "-",
        is_admin,
    )

    # =====================================================
    # SEND LOADING MESSAGE
    # =====================================================

    try:

        await message.answer(
            "⏳ Sedang menganalisa XAUUSD...\n\n"
            "M5 → SMC Structure\n"
            "M1 → Entry Timing\n"
            "OB / FVG / Liquidity\n"
            "Risk Management"
        )

    except Exception:

        logger.exception(
            "Gagal mengirim pesan proses analisa."
        )

        if quota_reserved:

            await refund_manual_quota(
                telegram_id,
                usage_date,
            )

        return

    # =====================================================
    # GENERATE SIGNAL
    # =====================================================

    try:

        signal = await asyncio.to_thread(
            generate_signal,
            structure_candle_count=12,
        )

    except NoTradeSignal as exc:

        logger.info(
            "MANUAL /signal -> NO TRADE | %s",
            exc,
        )

        if quota_reserved:

            await refund_manual_quota(
                telegram_id,
                usage_date,
            )

        await message.answer(
            "⚠️ NO TRADE\n\n"
            f"{str(exc)}\n\n"
            "Kuota request Anda tidak dipotong."
        )

        return

    except Exception:

        logger.exception(
            "ERROR GENERATE MANUAL SIGNAL"
        )

        if quota_reserved:

            await refund_manual_quota(
                telegram_id,
                usage_date,
            )

        await message.answer(
            "❌ Gagal membuat signal.\n\n"
            "Terjadi error pada engine analisa. "
            "Kuota request Anda tidak dipotong."
        )

        return

    # =====================================================
    # LOG SIGNAL
    # =====================================================

    logger.info(
        "MANUAL SIGNAL CREATED | "
        "bias=%s | entry=%s | order=%s | probability=%s%%",
        getattr(signal, "bias", "-"),
        getattr(signal, "entry_price", "-"),
        getattr(signal, "order_type", "-"),
        getattr(signal, "probability", "-"),
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

        if quota_reserved:

            await refund_manual_quota(
                telegram_id,
                usage_date,
            )

        await message.answer(
            "❌ Signal berhasil dianalisa, "
            "tetapi gagal memformat pesan.\n\n"
            "Kuota request Anda tidak dipotong."
        )

        return

    # =====================================================
    # SAVE SIGNAL DETAIL
    # =====================================================

    try:

        signal_id = save_signal(
            signal_text,
            detail_text,
        )

        logger.info(
            "SIGNAL STORE SAVED | signal_id=%s",
            signal_id,
        )

    except Exception:

        logger.exception(
            "ERROR SAVE SIGNAL + DETAIL"
        )

        signal_id = None

    # =====================================================
    # DETAIL BUTTON
    # =====================================================

    reply_markup = (
        detail_keyboard(signal_id)
        if signal_id
        else None
    )

    # =====================================================
    # SEND SIGNAL
    # =====================================================

    sent = False

    try:

        await message.answer(
            signal_text,
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

        sent = True

    except Exception:

        logger.exception(
            "ERROR SEND MANUAL SIGNAL WITH MARKDOWN"
        )

        # =================================================
        # FALLBACK WITHOUT MARKDOWN
        # =================================================

        try:

            await message.answer(
                signal_text,
                reply_markup=reply_markup,
            )

            sent = True

        except Exception:

            logger.exception(
                "FALLBACK SEND SIGNAL ALSO FAILED"
            )

    # =====================================================
    # SEND FAILED -> REFUND
    # =====================================================

    if not sent:

        if quota_reserved:

            await refund_manual_quota(
                telegram_id,
                usage_date,
            )

        await message.answer(
            "❌ Signal gagal dikirim. "
            "Kuota request Anda dikembalikan."
        )

        return

    # =====================================================
    # SUCCESS LOG
    # =====================================================

    if not is_admin:

        logger.info(
            "MEMBER MANUAL SIGNAL SUCCESS | "
            "telegram_id=%s | usage=%s/%s",
            telegram_id,
            used_count,
            daily_limit,
        )


# =========================================================
# SHOW DETAIL ANALISA
#
# Pesan signal lama diedit menjadi detail.
# Tidak mengirim pesan baru.
# =========================================================

@router.callback_query(
    F.data.startswith("detail:")
)
async def handle_detail_callback(
    callback: CallbackQuery,
):

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
            "DETAIL ANALISA SHOW | signal_id=%s",
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
# Pesan detail dikembalikan menjadi signal short.
# Tidak mengirim pesan baru.
# =========================================================

@router.callback_query(
    F.data.startswith("hide:")
)
async def handle_hide_callback(
    callback: CallbackQuery,
):

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
            "DETAIL ANALISA HIDE | signal_id=%s",
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
# Jalur ini menerima text biasa dari source group.
# Sinyal diteruskan kepada member aktif.
#
# Tidak menggunakan kuota manual /signal.
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
                chat_id=int(telegram_id),
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
