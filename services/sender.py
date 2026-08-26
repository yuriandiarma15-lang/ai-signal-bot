"""
services/sender.py

Telegram Signal Sender (aiogram)
=================================
"""

import asyncio
import logging

from typing import Any, Dict

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from services.membership import get_active_members
from services.signal_builder import (
    TradeSignal,
    format_signal_short,
    format_signal_detail,
)
from services.signal_store import save_detail


logger = logging.getLogger(__name__)

SEND_DELAY = 0.05
PARSE_MODE = "Markdown"


def format_trade_signal(signal) -> str:
    if isinstance(signal, str):
        return signal
    if isinstance(signal, TradeSignal):
        return format_signal_short(signal)
    try:
        return format_signal_short(signal)
    except Exception:
        logger.exception("Object signal tidak dapat diformat.")
        raise


async def send_signal_to_members(bot, signal_text) -> Dict[str, Any]:

    if bot is None:
        logger.error("Bot Telegram tidak tersedia.")
        return {"success": 0, "failed": 0, "total": 0}

    # =====================================================
    # SIAPKAN TOMBOL "DETAIL ANALISA" (hanya untuk TradeSignal)
    # =====================================================

    reply_markup = None

    if isinstance(signal_text, TradeSignal):
        detail_text = format_signal_detail(signal_text)
        signal_id = save_detail(detail_text)
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Detail Analisa", callback_data=f"detail:{signal_id}")]
            ]
        )

    try:
        signal_text = format_trade_signal(signal_text)
    except Exception:
        logger.exception("Gagal memformat signal.")
        return {"success": 0, "failed": 0, "total": 0}

    if not isinstance(signal_text, str):
        logger.error("Signal bukan string: %s", type(signal_text))
        return {"success": 0, "failed": 0, "total": 0}

    if not signal_text.strip():
        logger.error("Signal text kosong.")
        return {"success": 0, "failed": 0, "total": 0}

    try:
        members = get_active_members()
    except Exception:
        logger.exception("Gagal mengambil daftar member aktif.")
        return {"success": 0, "failed": 0, "total": 0}

    if not members:
        logger.warning("Tidak ada member aktif.")
        return {"success": 0, "failed": 0, "total": 0}

    total = len(members)
    success = 0
    failed = 0

    logger.info("Mulai mengirim signal ke %s member aktif.", total)

    for member in members:

        telegram_id = member.get("telegram_id")

        if not telegram_id:
            logger.warning("Telegram ID kosong: %s", member)
            failed += 1
            continue

        try:
            telegram_id = int(telegram_id)
        except (ValueError, TypeError):
            logger.warning("Telegram ID tidak valid: %s", telegram_id)
            failed += 1
            continue

        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=signal_text,
                parse_mode=PARSE_MODE,
                disable_web_page_preview=True,
                reply_markup=reply_markup,
            )
            success += 1
            logger.info("Signal TERKIRIM → %s", telegram_id)

        except Exception as e:
            failed += 1
            logger.error("Signal GAGAL → %s | %s", telegram_id, repr(e))

        if SEND_DELAY > 0:
            await asyncio.sleep(SEND_DELAY)

    result = {"success": success, "failed": failed, "total": total}

    logger.info(
        "Pengiriman signal selesai | success=%s | failed=%s | total=%s",
        success, failed, total,
    )

    return result
