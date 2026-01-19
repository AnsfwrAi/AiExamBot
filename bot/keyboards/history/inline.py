from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from django.conf import settings

def history_my_scripts():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='📝 Мои покупки: активные',
                    callback_data='history_my_scripts'
                ),
                InlineKeyboardButton(
                    text='📝 Мои покупки: неактивные',
                    callback_data='history_my_scripts_history'
                )
            ]
        ]
    )


def get_page_keyboard_sessions_history(current_page: int, total_pages: int, scripts_on_page: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    script_buttons = []
    for i, script in enumerate(scripts_on_page, 1):
        script_buttons.append(
            InlineKeyboardButton(
                text=f"{i}",
                callback_data=f"script_detail_{script['id']}"
            )
        )

    if script_buttons:
        builder.row(*script_buttons)

    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"scripts_page_{current_page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="current_page"
        )
    )

    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"scripts_page_{current_page + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    builder.row(
        InlineKeyboardButton(
            text="🔄 Обновить",
            callback_data="scripts_page_1"
        )
    )

    return builder.as_markup()


def get_detail_keyboard(script_key: str):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Изменить время;)",
                    web_app={"url": f"{settings.WEB_APP_REDACT_TIME_URL}?key={script_key}"},
                    callback_data=f"change_time:{script_key}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_scripts_list"
                )
            ]
        ]
    )