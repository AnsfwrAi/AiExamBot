from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot import CommandMap

def main_menu(lang):
    if lang != "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text=CommandMap.User.Uz.BUY_SCRIPT),
                    KeyboardButton(text=CommandMap.User.Uz.MY_SCRIPTS),
                ],
                [
                    KeyboardButton(text=CommandMap.User.Uz.MY_DATA),
                    KeyboardButton(text=CommandMap.User.Uz.INSTRUCTION)
                ],
                [
                    KeyboardButton(text=CommandMap.User.Uz.SUPPORT),
                ],
                [
                    KeyboardButton(text=CommandMap.User.Uz.LANGUAGE),
                ]
            ],
            resize_keyboard=True
        )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CommandMap.User.Ru.BUY_SCRIPT),
                KeyboardButton(text=CommandMap.User.Ru.MY_SCRIPTS),
            ],
            [
                KeyboardButton(text=CommandMap.User.Ru.MY_DATA),
                KeyboardButton(text=CommandMap.User.Ru.INSTRUCTION)
            ],
            [
                KeyboardButton(text=CommandMap.User.Ru.SUPPORT),
            ],
            [
                KeyboardButton(text=CommandMap.User.Ru.LANGUAGE),
            ]
        ],
        resize_keyboard=True
    )


