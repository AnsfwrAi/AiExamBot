from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def check_payment(redis_key):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"allow_payment_from_admin:{redis_key}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"deny_payment_from_admin:{redis_key}"
                )
            ]
        ]
    )

def dev_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📥 Получить метаданные файла",
                    callback_data="metadata_file",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📎 Get File by ID",
                    callback_data="get_file_by_id",
                )
            ]
        ]
    )