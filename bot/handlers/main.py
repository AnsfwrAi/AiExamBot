from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from asgiref.sync import sync_to_async
from django.conf import settings

from services.crypto import CompactReferralCipher
from services.models import operations
from ..keyboards.user import reply as user_reply, inline as user_inline
from ..keyboards.admin import reply as admin_reply, inline as admin_inline
from .. import bot
from ..filters import police


main = Router()

@main.message(CommandStart())
async def start_handler(message: types.Message, command: CommandStart):
    user_id = message.from_user.id
    referral_code = command.args
    ref_by = None

    if referral_code:
        try:
            ref_by = CompactReferralCipher().decrypt_id(referral_code)
            if ref_by == user_id or ref_by is None:
                ref_by = None
        except Exception as e:
            ref_by = None
            print(f"[REFERRAL ERROR] '{referral_code}': {e}")
    # else:
    #     await message.answer()
    user = await sync_to_async(operations.get_or_create_tg_user)(user_id, ref_by)
    user_language = user.get("language", "ru")

    username = message.from_user.username or ("Гость" if user_language == "ru" else "Mehmon")
    _ru = ("<b>🎓 Решение для прохождения тестов на Uchi, РЭШ, Foxford и др</b>\n\n"
        "Сервис показывает готовые ответы во время прохождения заданий.\n"
        "Работает прямо в браузере — без установки.\n\n"
        "✅ <b>Поддержка всех классов и предметов</b>\n"
        "✅ <b>Подсказки появляются в том же окне, где и тест</b>\n"
        "✅ <b>Удобный выбор времени — активируется по вашему расписанию</b>\n"
        "✅ <b>Поддержка всегда на связи</b>\n\n"
        "💸 <i>Пригласи друга — получи скидку.</i>")

    _uz = ("<b>🎓 Uchi, RYSh, Foxford va boshqa testlarni topshirish uchun yechim</b>\n\n"
        "Xizmat topshiriqlarni bajarish jarayonida tayyor javoblarni ko‘rsatadi.\n"
        "To‘g‘ridan-to‘g‘ri brauzerda ishlaydi — o‘rnatish talab qilinmaydi.\n\n"
        "✅ <b>Barcha sinflar va fanlar qo‘llab-quvvatlanadi</b>\n"
        "✅ <b>Maslahatlar test oynasining o‘zida chiqadi</b>\n"
        "✅ <b>Qulay vaqt tanlash — siz belgilagan jadval bo‘yicha faollashadi</b>\n"
        "✅ <b>Qo‘llab-quvvatlash xizmati doim aloqada</b>\n\n"
        "💸 <i>Do‘stingizni taklif qiling — chegirma oling.</i>")

    await message.answer(
        text=_ru if user_language == "ru" else _uz,
        parse_mode="HTML"
    )

    if not user.get("police", False):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✅ Принять политику" if user_language == "ru" else "✅ Qabul qilish",
                callback_data="accept_policy_main")]
        ])

        _ru_w = ("<b>🛡️ Прежде чем начать, пожалуйста, ознакомьтесь и примите политику использования.</b>\n\n"
                 "Нажмите кнопку ниже, чтобы подтвердить согласие.")
        _uz_w = ("<b>🛡️ Boshlashdan oldin, iltimos, foydalanish siyosati bilan tanishing va uni qabul qiling.</b>"
                 "Roziligingizni tasdiqlash uchun quyidagi tugmani bosing.")
        try:
            try:
                file = settings.POLICE_FILE_TG_ID_DOCUMENT_RU if user_language == "ru" else settings.POLICE_FILE_TG_ID_DOCUMENT_UZ
                await bot.send_document(
                    chat_id=user_id,
                    document=file,
                    caption=_ru_w if user_language == "ru" else _uz_w,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                return
            except Exception as e:
                await bot.send_message(
                    chat_id=user_id,
                    text=_ru_w if user_language == "ru" else _uz_w,
                    parse_mode="HTML",
                    reply_markup=kb
                )
                return
        except Exception as e:
            print(f"Error sending start policy prompt: {e}")
            await sync_to_async(operations.set_police)(user_id, True)

    if await sync_to_async(operations.is_admin)(user_id):
        await message.answer("✅ Вы вошли как администратор", reply_markup=admin_reply.main_menu())
    else:
        await message.answer(f"Привет, {username}!" if user_language == "ru" else f"Salom, {username}!", reply_markup=user_reply.main_menu(user_language))


@main.callback_query(F.data == "accept_policy_main")
async def accept_policy_handler(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass

    user_id = callback.from_user.id
    user_lang = await sync_to_async(operations.get_user_language)(user_id)
    await callback.answer("✅ Политика принята" if user_lang == "ru" else "✅ Siyosat qabul qilindi", show_alert=True)

    username = callback.from_user.username or ("Гость" if user_lang == "ru" else "Mehmon")

    await sync_to_async(operations.set_police)(user_id, True)

    if await sync_to_async(operations.is_admin)(user_id):
        await callback.message.answer("✅ Вы вошли как администратор", reply_markup=admin_reply.main_menu())
    else:
        await callback.message.answer(f"Привет, {username}!" if user_lang == "ru" else f"Salom, {username}!", reply_markup=user_reply.main_menu(user_lang))
