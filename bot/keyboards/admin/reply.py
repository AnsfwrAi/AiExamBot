from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot import CommandMap

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=CommandMap.Admin.BUY_SCRIPT),
                KeyboardButton(text=CommandMap.Admin.MY_SCRIPTS),
            ],
            [
                KeyboardButton(text=CommandMap.Admin.MY_DATA),
                KeyboardButton(text=CommandMap.Admin.INSTRUCTION)
            ],
            [
                KeyboardButton(text=CommandMap.Admin.SUPPORT),
            ],
            [
                KeyboardButton(text=CommandMap.Admin.DEV_MENU),
            ]
        ],
        resize_keyboard=True
    )
