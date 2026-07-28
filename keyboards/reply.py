from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton
)



def main_keyboard():

    keyboard = ReplyKeyboardMarkup(

        keyboard=[

            [

                KeyboardButton(
                    text="/start"
                ),

                KeyboardButton(
                    text="/menu"
                )

            ]

        ],

        resize_keyboard=True

    )


    return keyboard
