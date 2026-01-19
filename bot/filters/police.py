from aiogram.filters import BaseFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from aiogram.exceptions import TelegramBadRequest

from django.conf import settings

from .. import bot
from ..keyboards.user import inline
from services.models import operations

class HasAcceptedPolicy(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        user = await sync_to_async(operations.get_or_create_tg_user)(user_id=message.from_user.id, ref_by=None)
        user_lang = user.get("language", "ru")

        if not user.get("police", False):
            try:
                await message.delete()
            except Exception:
                pass

            _ru_w = ("<b>🛡️ Прежде чем начать, пожалуйста, ознакомьтесь и примите политику использования.</b>\n\n"
                     "Нажмите кнопку ниже, чтобы подтвердить согласие.")
            _uz_w = ("<b>🛡️ Boshlashdan oldin, iltimos, foydalanish siyosati bilan tanishing va uni qabul qiling.</b>"
                     "Roziligingizni tasdiqlash uchun quyidagi tugmani bosing.")
            try:

                await bot.send_document(
                    chat_id=message.from_user.id,
                    document=settings.POLICE_FILE_TG_ID_DOCUMENT_RU if user_lang == "ru" else settings.POLICE_FILE_TG_ID_DOCUMENT_UZ,
                    caption=_ru_w if user_lang == "ru" else _uz_w,
                    parse_mode="HTML",
                    reply_markup=inline.police_kb()
                )
            except TelegramBadRequest:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=_ru_w if user_lang == "ru" else _uz_w,
                    parse_mode="HTML",
                    reply_markup=inline.police_kb()
                )
            except Exception:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=_ru_w if user_lang == "ru" else _uz_w,
                    parse_mode="HTML",
                    reply_markup=inline.police_kb()
                )

            return False
        return True