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
        - AI SMC
        - Materi

    PREMIUM:
        - AI SMC
        - Fundamental
        - Combined AI
        - Materi

    Semua tombol menggunakan:
        callback_data
    atau
        url

    Tidak menggunakan Text button.
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

    admin_username = str(
        ADMIN_USERNAME or ""
    ).strip().replace(
        "@",
        ""
    )


    if admin_username:

        buttons.append([

            InlineKeyboardButton(
                text="📞 Hubungi Admin",
                url=(
                    f"https://t.me/"
                    f"{admin_username}"
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

    renew_url = str(
        RENEW_BOT or ""
    ).strip()


    if renew_url:

        buttons.append([

            InlineKeyboardButton(
                text="🔄 Perpanjang Membership",
                url=renew_url
            )

        ])


    # =====================================================
    # RETURN
    # =====================================================

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )
