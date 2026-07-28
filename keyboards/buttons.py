from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


from config.settings import (
    RENEW_BOT
)





# ==========================
# RENEW BUTTON
# ==========================


def renew_button():


    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[

            [

                InlineKeyboardButton(

                    text="🔄 PERPANJANG MEMBERSHIP",

                    url=RENEW_BOT

                )

            ]

        ]

    )


    return keyboard
