from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


from config.settings import (
    ADMIN_USERNAME,
    RENEW_BOT
)





def member_menu():


    keyboard = InlineKeyboardMarkup(

        inline_keyboard=[


            [

                InlineKeyboardButton(

                    text="📞 Hubungi Admin",

                    url=
                    f"https://t.me/{ADMIN_USERNAME.replace('@','')}"

                )

            ],


            [

                InlineKeyboardButton(

                    text="⏳ Masa Membership",

                    callback_data="check_expired"

                )

            ],


            [

                InlineKeyboardButton(

                    text="🔄 Perpanjang Membership",

                    url=RENEW_BOT

                )

            ]


        ]

    )


    return keyboard
