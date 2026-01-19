import json
from aiogram import Router, F, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.conf import settings

from services.models import operations
from ... import redis, bot

admin_callback = Router()


@admin_callback.callback_query(F.data.regexp(r"allow_payment_from_admin:(.+)$"))
async def allow_payment_from_admin_handler(callback: types.CallbackQuery, state: FSMContext):
    redis_key = callback.data.split("allow_payment_from_admin:")[1]
    raw_data = json.loads(await redis.get(f"buy_script:{redis_key}"))

    key = raw_data.get("key")
    change_script = await sync_to_async(operations.change_script_status)(key, True)

    referrals_bonus_count = raw_data.get("referrals_count")

    if referrals_bonus_count:
        for _ in referrals_bonus_count:
            await sync_to_async(operations.change_status_referral_by_id)(
                referral_id=_.get("id"),
                status=True
            )

    _ru_user_message_text = (
        f"✅ Оплата подтверждена\n\n"
        f"Ваша оплата успешно получена и подтверждена.\n"
        f"Решение будет автоматически активировано в указанный промежуток времени:\n\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"⏱️ Начало: {change_script.get('start_at')}\n"
        f"⏱️ Окончание: {change_script.get('stop_at')}\n\n"
        f"🔗 Ссылка на решение:\n"
        f"<code>javascript:import('{settings.GET_SCRIPT_JS}/{change_script.get('script')}')</code>\n\n"
        f"📌 Пожалуйста, будьте на связи в этот период — система включится автоматически."
    )

    _uz_user_message_text = (
        f"✅ To‘lov tasdiqlandi\n\n"
        f"To‘lovingiz muvaffaqiyatli qabul qilindi va tasdiqlandi.\n"
        f"Yechim belgilangan vaqt oralig‘ida avtomatik tarzda faollashadi:\n\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"⏱️ Boshlanishi: {change_script.get('start_at')}\n"
        f"⏱️ Tugashi: {change_script.get('stop_at')}\n\n"
        f"🔗 Yechim havolasi:\n"
        f"<code>javascript:import('{settings.GET_SCRIPT_JS}/{change_script.get('script')}')</code>\n\n"
        f"📌 Iltimos, ushbu vaqt davomida aloqada bo‘ling — tizim avtomatik ishga tushadi."
    )

    user_lang = await sync_to_async(operations.get_user_language)(raw_data.get("user_id"))

    await bot.send_photo(
        chat_id=raw_data.get("user_id"),
        photo=raw_data.get("file_id"),
        caption=_ru_user_message_text if user_lang == "ru" else _uz_user_message_text,
        parse_mode="HTML"
    )

    testing_script_name = f"testing_{raw_data.get('script')}"
    testing_script = await sync_to_async(operations.create_testing_script)(testing_script_name)

    def _fmt(dt):
        return dt.strftime("%Y-%m-%d %H:%M")

    _ru_testing_block = (
        f"🧪 <b>Тестовое решение</b>\n"
        f"🆔 <code>{testing_script.get('key')}</code>\n"
        f"⏱️ Доступен: <code>{_fmt(testing_script.get('start_at'))}</code> — <code>{_fmt(testing_script.get('stop_at'))}</code>\n"
        f"🔗 <b>Ссылка для вставки в браузере:</b>\n"
        f"<code>javascript:import('{settings.GET_SCRIPT_JS}/{testing_script.get('script')}')</code>\n\n"
        f"📌 <b>Как использовать:</b>\n"
        f"1. Открой сайт: https://test.aft.ink/\n"
        f"2. Вставь эту ссылку в адресную строку браузера и нажми Enter\n"
        f"3. Система загрузит скрипт для тестирования интерфейса\n\n"
        f"❗ Используй только в современных браузерах (Chrome / Edge / Firefox)."
    )

    _uz_testing_block = (
        f"🧪 <b>Test yechimi</b>\n"
        f"🆔 <code>{testing_script.get('key')}</code>\n"
        f"⏱️ Mavjud: <code>{_fmt(testing_script.get('start_at'))}</code> — <code>{_fmt(testing_script.get('stop_at'))}</code>\n"
        f"🔗 <b>Brauzerga kiritish uchun havola:</b>\n"
        f"<code>javascript:import('{settings.GET_SCRIPT_JS}/{testing_script.get('script')}')</code>\n\n"
        f"📌 <b>Qanday foydalaniladi:</b>\n"
        f"1. Saytni oching: https://test.aft.ink/\n"
        f"2. Ushbu havolani brauzer manzil satriga joylashtiring va Enter tugmasini bosing\n"
        f"3. Tizim interfeysni sinovdan o‘tkazish uchun skriptni yuklaydi\n\n"
        f"❗ Faqat zamonaviy brauzerlarda foydalaning (Chrome / Edge / Firefox)."
    )

    try:
        vid = settings.VIDEO_INSTRUCTION_TG_ID_VIDEO_RU if user_lang == "ru" else settings.VIDEO_INSTRUCTION_TG_ID_VIDEO_UZ
        await bot.send_video(
            chat_id=raw_data.get("user_id"),
            video=vid,
            caption=_ru_testing_block if user_lang == "ru" else _uz_testing_block,
            parse_mode="HTML"
        )
    except Exception as e:
        await bot.send_message(
            chat_id=raw_data.get("user_id"),
            text=_ru_testing_block if user_lang == "ru" else _uz_testing_block,
            parse_mode="HTML"
        )

    chat = await bot.get_chat(raw_data.get('user_id'))
    user_name = "@" + str(chat.username) if chat.username else 'скрыт'

    caption = (
        f"User_id: {raw_data.get('user_id')}\n"
        f"user_name: {user_name}\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"💵 Сумма: <b>{raw_data.get('payment_sum')}</b>\n"
        f"⏱️ С:  <code>{raw_data.get('start_at')}</code>\n"
        f"⏱️ До: <code>{raw_data.get('stop_at')}</code>\n\n"
        f"✅ <b>Оплата подтверждена</b>"
    )

    for admin, msg_id in raw_data.get("admins").items():
        try:
            await bot.edit_message_caption(
                chat_id=int(admin),
                message_id=msg_id,
                caption=caption,
                reply_markup=None,
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise


    if raw_data.get("referred_by"):
        await sync_to_async(operations.add_to_referral)(
            inviter_user_id=raw_data.get("referred_by"),
            invited_user_id=raw_data.get("user_id")
        )

    try:
        await bot.delete_message(
            chat_id=raw_data.get("user_id"),
            message_id=raw_data.get("payment_msg_id")
        )
    except:
        pass

    try:
        await bot.delete_message(
            chat_id=raw_data.get("user_id"),
            message_id=raw_data.get("send_payment_msg_id")
        )
    except:
        pass
    await state.clear()
    await redis.delete(f"buy_script:{redis_key}")


@admin_callback.callback_query(F.data.regexp(r"deny_payment_from_admin:(.+)$"))
async def deny_payment_from_admin_handler(callback: types.CallbackQuery, state: FSMContext):
    redis_key = callback.data.split("deny_payment_from_admin:")[1]
    raw_data = json.loads(await redis.get(f"buy_script:{redis_key}"))
    key = raw_data.get("key")

    referrals_bonus_count = raw_data.get("referrals_count")
    if referrals_bonus_count:
        for _ in referrals_bonus_count:
            await sync_to_async(operations.change_status_referral_by_id)(
                referral_id=_.get("id"),
                status=False
            )

    _ru_user_message_text = (
        f"❌ Оплата отклонена\n\n"
        f"К сожалению, ваша оплата не была подтверждена администратором.\n"
        f"Если вы считаете, что произошла ошибка — свяжитесь с поддержкой или админом вручную.\n\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"💵 Сумма: <b>{raw_data.get('payment_sum')}</b>\n"
        f"⏱️ С: <code>{raw_data.get('start_at')}</code>\n"
        f"⏱️ До: <code>{raw_data.get('stop_at')}</code>\n\n"
    )

    _uz_user_message_text = (
        f"❌ To‘lov rad etildi\n\n"
        f"Afsuski, to‘lovingiz administrator tomonidan tasdiqlanmadi.\n"
        f"Agar bu xato deb hisoblasangiz — qo‘llab-quvvatlash xizmatiga murojaat qiling yoki administrator bilan qo‘lda bog‘laning.\n\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"💵 Miqdor: <b>{raw_data.get('payment_sum')}</b>\n"
        f"⏱️ Dan: <code>{raw_data.get('start_at')}</code>\n"
        f"⏱️ Gacha: <code>{raw_data.get('stop_at')}</code>\n\n"
    )

    user_lang = await sync_to_async(operations.get_user_language)(raw_data.get("user_id"))

    await bot.send_photo(
        chat_id=raw_data.get("user_id"),
        photo=raw_data.get("file_id"),
        caption=_ru_user_message_text if user_lang == "ru" else _uz_user_message_text,
        parse_mode="HTML"
    )

    chat = await bot.get_chat(raw_data.get('user_id'))
    user_name = "@" + str(chat.username) if chat.username else 'скрыт'
    caption_2 = (
        f"User_id: {raw_data.get('user_id')}\n"
        f"user_name: {user_name}\n"
        f"🆔: <code>{raw_data.get('key')}</code>\n\n"
        f"💵 Сумма: <b>{raw_data.get('payment_sum')}</b>\n"
        f"⏱️ С:  <code>{raw_data.get('start_at')}</code>\n"
        f"⏱️ До: <code>{raw_data.get('stop_at')}</code>\n\n"
        f"❌ <b>Оплата отклонена </b>"
    )

    for admin, msg_id in raw_data.get("admins").items():
        try:
            await bot.edit_message_caption(
                chat_id=int(admin),
                message_id=msg_id,
                caption=caption_2,
                parse_mode="HTML",
                reply_markup=None
            )
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                pass
            else:
                raise

    try:
        await bot.delete_message(
            chat_id=raw_data.get("user_id"),
            message_id=raw_data.get("payment_msg_id")
        )
    except:
        pass

    try:
        await bot.delete_message(
            chat_id=raw_data.get("user_id"),
            message_id=raw_data.get("send_payment_msg_id")
        )
    except:
        pass

    await state.clear()
    await redis.delete(f"buy_script:{redis_key}")
