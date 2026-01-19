from aiogram import Router, F, types
from asgiref.sync import sync_to_async

from .. import CommandMap
from ..keyboards.user import reply as user_reply
from services.models import operations

lang_router = Router()


@lang_router.message(F.text.in_([CommandMap.User.Ru.LANGUAGE, CommandMap.User.Uz.LANGUAGE]))
async def change_language_handler(message: types.Message):
    user_id = message.from_user.id
    __user = await sync_to_async(operations.get_or_create_tg_user)(user_id)

    kb = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="🇷🇺 Русский",
                    callback_data="set_language:ru"
                )
            ],
            [
                types.InlineKeyboardButton(
                    text="🇺🇿 O'zbekcha",
                    callback_data="set_language:uz"
                )
            ]
        ]
    )
    await message.answer(
        "🌐 Пожалуйста, выберите язык / Iltimos, tilni tanlang:",
        reply_markup=kb
    )

@lang_router.callback_query(F.data.regexp(r"set_language:(.+)$"))
async def set_language_handler(callback: types.CallbackQuery):
    lang_code = callback.data.split("set_language:")[1]

    if lang_code not in ("ru", "uz"):
        await callback.answer(
            "⛔ Неверный выбор языка / Noto‘g‘ri til tanlandi",
            show_alert=True
        )
        return
    await callback.message.delete()

    await sync_to_async(operations.set_user_language)(callback.from_user.id, lang_code)

    await callback.message.answer(
        "✅ Язык успешно изменён." if lang_code == "ru" else "✅ Til muvaffaqiyatli o'zgartirildi.",
        parse_mode="HTML",
        reply_markup=user_reply.main_menu(lang_code)
    )
