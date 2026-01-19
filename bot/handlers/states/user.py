from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
import json

from ... fsm.user import UserPaymentCheck
from ... fsm.admin import AdminPaymentCheck
from ... import bot, redis
from .. user import admin_inline, user_inline
from services.models import operations

state_user = Router()


@state_user.message(UserPaymentCheck.waiting_for_img, F.photo)
async def get_payment_img(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass

    redis_data = await state.get_data()
    redis_key = redis_data.get("redis_key")

    if not redis_key:
        await state.clear()
        return

    raw_data = await redis.get(f"buy_script:{redis_key}")
    if not raw_data:
        return
    data = json.loads(raw_data)

    payment_msg_id = data.get("payment_msg_id")

    try:
        await bot.edit_message_reply_markup(
            chat_id=message.from_user.id,
            message_id=payment_msg_id,
            reply_markup=None
        )
    except:
        pass

    if data.get("error_msg_id"):
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=data.get("error_msg_id")
            )
        except:
            pass

    photo = message.photo[-1]
    file_id = photo.file_id

    await state.set_state(UserPaymentCheck.waiting_for_accept)

    data["file_id"] = file_id
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))

    resend_msg_id = data.get("resend_msg_id")
    if resend_msg_id:
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=resend_msg_id
            )
        except:
            pass

    if data.get("err_warning_message_id"):
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=data.get("err_warning_message_id")
            )
        except:
            pass
    user_lang = await sync_to_async(operations.get_user_language)(message.from_user.id)
    _ru_caption = (
        f"🆔 <code>{data.get('key')}</code>\n"
        f"⏱ <b>Начало:</b> <code>{data.get('start_at')}</code>\n"
        f"⏳ <b>Конец:</b> <code>{data.get('stop_at')}</code>\n\n"
        f"💰 <b>Сумма:</b> <code>{data.get('payment_sum')}</code> сум"
    )
    _uz_caption = (
        f"🆔 <code>{data.get('key')}</code>\n"
        f"⏱ <b>Boshlanishi:</b> <code>{data.get('start_at')}</code>\n"
        f"⏳ <b>Tugashi:</b> <code>{data.get('stop_at')}</code>\n\n"
        f"💰 <b>To‘lov summasi:</b> <code>{data.get('payment_sum')}</code> so'm"
    )

    caption = _ru_caption if user_lang == "ru" else _uz_caption
    msg = await bot.send_photo(
        chat_id=message.from_user.id,
        photo=file_id,
        caption=caption,
        reply_markup=user_inline.send_or_receive_payment(redis_key, user_language=user_lang),
        parse_mode="HTML"
    )

    data["send_payment_msg_id"] = msg.message_id
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))
    await state.clear()

@state_user.message(UserPaymentCheck.waiting_for_img)
async def handle_not_photo(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass

    redis_data = await state.get_data()
    redis_key = redis_data.get("redis_key")

    raw_data = await redis.get(f"buy_script:{redis_key}")
    if not raw_data:
        return
    data = json.loads(raw_data)

    try:
        await bot.edit_message_reply_markup(
                chat_id=message.from_user.id,
                message_id=data.get("payment_msg_id"),
                reply_markup=None
            )
    except:
        pass

    if data.get("error_msg_id"):
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=data.get("error_msg_id")
            )
        except:
            pass

    if data.get("resend_msg_id"):
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=data.get("resend_msg_id")
            )
        except:
            pass

    if data.get("err_warning_message_id"):
        try:
            await bot.delete_message(
                chat_id=message.from_user.id,
                message_id=data.get("err_warning_message_id")
            )
        except:
            pass

    user_lang = await sync_to_async(operations.get_user_language)(message.from_user.id)
    _ru_dont_image = (
        "❌ <b>Нужно отправить именно фото</b>\n\n"
        "Пожалуйста, прикрепи <u>скриншот или фото чека</u> как изображение.\n\n"
        "Или же можете отменить покупку."
    )
    _uz_dont_image = (
        "❌ <b>Aynan rasm yuborish kerak</b>\n\n"
        "Iltimos, <u>chekning skrinshoti yoki fotosuratini</u> rasm sifatida yuboring.\n\n"
        "Yoki xaridni bekor qilishingiz mumkin."
    )

    err_dont_image_message = await message.answer(
        _ru_dont_image if user_lang == "ru" else _uz_dont_image,
        parse_mode="HTML",
        reply_markup=user_inline.cancel_keyboard(redis_key=redis_key, user_language=user_lang) if redis_key else None
    )


    data["error_msg_id"] = err_dont_image_message.message_id
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))
