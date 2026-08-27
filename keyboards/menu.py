from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config.settings import (
    ADMIN_USERNAME,
    RENEW_BOT
)

from services.membership import (
    has_smc_access,
    has_fundamental_access,
    has_combined_access
)


# =========================================================
# MEMBER MENU
# =========================================================

def member_menu(member):
    """
    Membuat menu berdasarkan jenis membership.

    BASIC:
        1 Bulan
        MITRA HFM

    PREMIUM:
        6 Bulan
        12 Bulan
        Lifetime

    Semua member ACTIVE mendapatkan:
        - AI SMC
        - Materi

    Premium mendapatkan:
        - Fundamental
        - Combined AI
    """

    buttons = []


    # =====================================================
    # AI SMC
    # =====================================================

    if has_smc_access(member):

        buttons.append([

            InlineKeyboardButton(
                text="🤖 AI SMC",
                callback_data="ai_smc"
            )

        ])


    # =====================================================
    # FUNDAMENTAL
    # =====================================================

    if has_fundamental_access(member):

        buttons.append([

            InlineKeyboardButton(
                text="📰 FUNDAMENTAL",
                callback_data="fundamental"
            )

        ])


    # =====================================================
    # COMBINED AI
    # =====================================================

    if has_combined_access(member):

        buttons.append([

            InlineKeyboardButton(
                text="🧠 COMBINED AI",
                callback_data="combined_ai"
            )

        ])


    # =====================================================
    # MATERI
    # =====================================================

    buttons.append([

        InlineKeyboardButton(
            text="📚 MATERI",
            callback_data="materi"
        )

    ])


    # =====================================================
    # ADMIN
    # =====================================================

    buttons.append([

        InlineKeyboardButton(

            text="📞 Hubungi Admin",

            url=(
                f"https://t.me/"
                f"{ADMIN_USERNAME.replace('@', '')}"
            )

        )

    ])


    # =====================================================
    # MEMBERSHIP
    # =====================================================

    buttons.append([

        InlineKeyboardButton(
            text="⏳ Masa Membership",
            callback_data="check_expired"
        )

    ])


    # =====================================================
    # RENEW
    # =====================================================

    buttons.append([

        InlineKeyboardButton(
            text="🔄 Perpanjang Membership",
            url=RENEW_BOT
        )

    ])


    # =====================================================
    # RETURN KEYBOARD
    # =====================================================

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
