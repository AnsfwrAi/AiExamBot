from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.conf import settings

def cancel_keyboard(redis_key, user_language: str):
    text = '❌Отменить' if user_language == 'ru' else '❌ Bekor qilish'

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f'cancel_payment:{redis_key}'
                )
            ]
        ]
    )


def select_time(user_language: str):
    text = '📅Выбрать время' if user_language == 'ru' else '📅 Vaqtni tanlash'

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    web_app={"url": settings.WEB_APP_SELECT_TIME_URL}
                )
            ]
        ]
    )

def support(user_language: str):
    is_ru = user_language == "ru"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📚 Популярные вопросы" if is_ru else "📚 Ommabop savollar",
                    callback_data="faq"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📩 Написать администратору" if is_ru else "📩 Administratorga yozish",
                    url="https://t.me/AFT_Admin1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📘 Читать политику" if is_ru else "📘 Siyosatni o‘qish",
                    callback_data="read_policy"
                )
            ]
        ]
    )

def back_support(user_language: str):
    text = "🔙 Назад" if user_language == "ru" else "🔙 Orqaga"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=text, callback_data="back_to_support")
            ]
        ]
    )


def send_or_receive_payment(redis_key, user_language: str) -> InlineKeyboardMarkup:
    is_ru = user_language == "ru"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Отправить на проверку" if is_ru else "📤 Tekshiruvga yuborish",
                    callback_data=f"send_pay:{redis_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 Заново отправить чек" if is_ru else "📥 Chekni qayta yuborish",
                    callback_data=f"resend_pay:{redis_key}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌Отменить" if is_ru else "❌ Bekor qilish",
                    callback_data=f"cancel_payment:{redis_key}",
                )
            ]
        ]
    )


def change_buy(redis_key, user_language: str):
    text = "Оплатить" if user_language == "ru" else "To‘lash"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"buy_script:{redis_key}"
                )
            ]
        ]
    )


def police_kb(user_language: str):
    text = "✅ Принять политику" if user_language == "ru" else "✅ Siyosatni qabul qilish"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data="accept_policy"
                )
            ]
        ]
    )
