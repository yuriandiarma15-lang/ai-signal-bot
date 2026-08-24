"""
Telegram Signal Sender

Fungsi:
- Mengambil seluruh member aktif
- Mengirim signal ke masing-masing member
- Menerima signal berupa string ATAU TradeSignal object
- Otomatis melakukan konversi TradeSignal -> string
- Menggunakan Markdown
"""

import asyncio
import logging

from typing import Any, Dict


from services.membership import (
    get_active_members
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
# FORMAT TRADE SIGNAL
# =========================================================

def format_trade_signal(
    signal
) -> str:

    """
    Mengubah TradeSignal object
    menjadi text Telegram.

    Jika signal sudah berupa string,
    langsung dikembalikan.
    """

    # =====================================================
    # SUDAH STRING
    # =====================================================

    if isinstance(
        signal,
        str
    ):

        return signal


    # =====================================================
    # AMBIL ATTRIBUTE DENGAN AMAN
    # =====================================================

    def get_attr(
        name,
        default="-"
    ):

        value = getattr(
            signal,
            name,
            default
        )

        if value is None:

            return default

        return value


    # =====================================================
    # DATA UTAMA
    # =====================================================

    timestamp = get_attr(
        "timestamp",
        "-"
    )

    bias = get_attr(
        "bias",
        "-"
    )

    entry_price = get_attr(
        "entry_price",
        "-"
    )

    entry_type = get_attr(
        "entry_type",
        "-"
    )

    order_type = get_attr(
        "order_type",
        "-"
    )

    is_pending = get_attr(
        "is_pending",
        False
    )

    sl = get_attr(
        "sl",
        "-"
    )

    tp1 = get_attr(
        "tp1",
        "-"
    )

    tp2 = get_attr(
        "tp2",
        "-"
    )

    probability = get_attr(
        "probability",
        "-"
    )


    # =====================================================
    # TAMBAHAN SMC
    # =====================================================

    smc = get_attr(
        "smc",
        None
    )

    zone = "-"

    if smc is not None:

        zone = getattr(
            smc,
            "zone",
            "-"
        )

        if zone == "-":

            zone = getattr(
                smc,
                "entry_zone",
                "-"
            )


    # =====================================================
    # RR
    # =====================================================

    rr_tp1 = get_attr(
        "rr_tp1",
        "-"
    )

    rr_tp2 = get_attr(
        "rr_tp2",
        "-"
    )


    # =====================================================
    # REASONS
    # =====================================================

    reasons = get_attr(
        "reasons",
        []
    )


    if reasons is None:

        reasons = []


    if isinstance(
        reasons,
        str
    ):

        reasons = [
            reasons
        ]


    # =====================================================
    # BUILD REASON TEXT
    # =====================================================

    reason_text = ""


    for reason in reasons:

        if reason:

            reason_text += (
                f"• {reason}\n"
            )


    if not reason_text:

        reason_text = (
            "• Konfirmasi struktur "
            "SMC dan price action\n"
        )


    # =====================================================
    # NORMALISASI BIAS
    # =====================================================

    bias_text = str(
        bias
    ).upper()


    if (
        "BULL" in bias_text
    ):

        direction = "🟢 BUY"

    elif (
        "BEAR" in bias_text
    ):

        direction = "🔴 SELL"

    else:

        direction = bias_text


    # =====================================================
    # ORDER TYPE
    # =====================================================

    if is_pending:

        order_text = (
            f"Pending {order_type}"
        )

    else:

        order_text = (
            "Market"
        )


    # =====================================================
    # FORMAT
    # =====================================================

    text = (

        "📢 *XAUUSD M5 SMC SIGNAL*\n"
        "\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"📅 *Time:* `{timestamp}`\n"

        f"📊 *Bias:* {direction}\n"

        f"🎯 *Entry:* `{entry_price}`\n"

        f"⚡ *Type:* {entry_type}\n"

        f"📌 *Order:* {order_text}\n"

        f"📍 *Zone:* {zone}\n"

        "\n"

        "━━━━━━━━━━━━━━━━━━\n"

        "🛡️ *RISK MANAGEMENT*\n"

        f"❌ *SL:* `{sl}`\n"

        f"🎯 *TP1:* `{tp1}`\n"

        f"🚀 *TP2:* `{tp2}`\n"

        f"📐 *RR TP1:* `{rr_tp1}`\n"

        f"📐 *RR TP2:* `{rr_tp2}`\n"

        "\n"

        "━━━━━━━━━━━━━━━━━━\n"

        f"🔥 *Probability:* `{probability}%`\n"

        "\n"

        "🧠 *SMC REASONING*\n"

        f"{reason_text}"

        "\n"

        "━━━━━━━━━━━━━━━━━━\n"

        "🤖 *XAU AI SMC GOLD*\n"

        "⚠️ Gunakan risk management."

    )


    return text


# =========================================================
# SEND SIGNAL TO MEMBERS
# =========================================================

async def send_signal_to_members(
    bot,
    signal_text
) -> Dict[str, Any]:

    """
    Kirim signal ke seluruh member aktif.

    signal_text boleh berupa:

    - str
    - TradeSignal object

    Jika TradeSignal object,
    otomatis dikonversi menjadi text.
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
            "Gagal memformat TradeSignal."
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
        str
    ):

        logger.error(
            "Signal bukan string: %s",
            type(signal_text)
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
        total
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
                member
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
            TypeError
        ):

            logger.warning(
                "Telegram ID tidak valid: %s",
                telegram_id
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

                disable_web_page_preview=True

            )


            success += 1


            logger.info(
                "Signal TERKIRIM → %s",
                telegram_id
            )


        except Exception as e:

            failed += 1


            logger.error(
                "Signal GAGAL → %s | %s",
                telegram_id,
                repr(e)
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

        total

    )


    return result
