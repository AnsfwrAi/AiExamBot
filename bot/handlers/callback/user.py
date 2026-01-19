import json
from aiogram import Router, F, types, exceptions
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async
from django.conf import settings

from .. user import user_inline, admin_inline
from ... import redis, bot
from ... fsm.user import UserPaymentCheck

from services.models import operations


user_callback = Router()

@user_callback.callback_query(F.data == "faq")
async def show_faq(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)

    if current_state == UserPaymentCheck.waiting_for_img:
        try:
            await callback.message.delete()
        except:
            pass

        redis_data = await state.get_data()
        redis_key = redis_data.get("redis_key")
        raw_data = await redis.get(f"buy_script:{redis_key}")
        if not raw_data:
            return
        data = json.loads(raw_data)

        _ru_text_warning = "⛔ Сначала завершите текущую оплату — отправьте фото чека.\nИли отмените оплату"
        _uz_text_warning = "⛔ Avval joriy to‘lovni yakunlang — chek fotosuratini yuboring.\nYoki to‘lovni bekor qiling"

        try:
            await bot.edit_message_reply_markup(
                chat_id=callback.message.from_user.id,
                message_id=data.get("payment_msg_id"),
                reply_markup=None
            )
        except:
            pass

        if data.get("error_msg_id"):
            try:
                await bot.delete_message(
                    chat_id=callback.message.from_user.id,
                    message_id=data.get("error_msg_id")
                )
            except:
                pass

        if data.get("resend_msg_id"):
            try:
                await bot.delete_message(
                    chat_id=callback.message.from_user.id,
                    message_id=data.get("resend_msg_id")
                )
            except:
                pass

        if data.get("err_warning_message_id"):
            try:
                await bot.delete_message(
                    chat_id=callback.message.from_user.id,
                    message_id=data.get("err_warning_message_id")
                )
            except:
                pass

        err_warning_message = await callback.message.answer(
            _ru_text_warning if user_lang == "ru" else _uz_text_warning,
            reply_markup=user_inline.cancel_keyboard(redis_key, user_lang)
        )
        data["err_warning_message_id"] = err_warning_message.message_id
        await redis.set(f"buy_script:{redis_key}", json.dumps(data))
        return

    await callback.answer()

    _ru_faq_text = (
        "<b>📚 Популярные вопросы</b>\n\n"

        "1. 👥 <b>Как работает реферальная программа?</b>\n"
        "Вы приглашаете людей. Если кто-то из них совершит покупку, вы получите скидку 25 000 сум. "
        "Максимальная скидка — 125 000 сум на одну покупку.\n\n"

        "2. 🕒 <b>Когда активируется скрипт?</b>\n"
        "Скрипт будет работать ровно 2 часа с выбранного вами времени. "
        "Например, если вы выбрали 14:30 — скрипт будет активен с 14:30 до 16:30.\n\n"

        "3. 💰 <b>Как происходит оплата?</b>\n"
        "После выбора времени вы получите сумму. Оплатите удобным способом и отправьте боту скриншот чека для активации скрипта.\n\n"

        "4. 🚫 <b>Можно ли вернуть деньги?</b>\n"
        "Нет. Возврат средств не предусмотрен. Перед оплатой внимательно проверьте всё.\n\n"

        "5. 🔐 <b>Насколько это безопасно?</b>\n"
        "Мы используем Telegram WebApp. Данные надежно защищены, и ничего лишнего не сохраняется.\n\n"

        "6. 📩 <b>К кому обращаться с вопросами?</b>\n"
        "Свяжитесь с админом: @AFT_Admin1"
    )

    _uz_faq_text = (
        "<b>📚 Ko‘p beriladigan savollar</b>\n\n"

        "1. 👥 <b>Referal dasturi qanday ishlaydi?</b>\n"
        "Siz foydalanuvchilarni taklif qilasiz. Agar ular xarid qilsa, "
        "siz 25 000 so‘m chegirma olasiz. Maksimal chegirma — 125 000 so‘m.\n\n"

        "2. 🕒 <b>Skript qachon faollashadi?</b>\n"
        "Skript tanlangan vaqtdan boshlab aniq 2 soat ishlaydi. "
        "Masalan, 14:30 dan 16:30 gacha.\n\n"

        "3. 💰 <b>To‘lov qanday amalga oshiriladi?</b>\n"
        "Vaqtni tanlagach, summa ko‘rsatiladi. To‘lovni amalga oshiring "
        "va chek rasmini botga yuboring.\n\n"

        "4. 🚫 <b>Pulni qaytarish mumkinmi?</b>\n"
        "Yo‘q. Pul qaytarilmaydi. To‘lovdan oldin hammasini tekshiring.\n\n"

        "5. 🔐 <b>Bu qanchalik xavfsiz?</b>\n"
        "Telegram WebApp ishlatiladi. Ma’lumotlar himoyalangan.\n\n"

        "6. 📩 <b>Savollar bo‘lsa kimga murojaat qilish kerak?</b>\n"
        "Admin bilan bog‘laning: @AFT_Admin1"
    )

    await callback.message.edit_text(
        _ru_faq_text if user_lang == "ru" else _uz_faq_text,
        parse_mode="HTML",
        reply_markup=user_inline.back_support(user_lang)
    )


@user_callback.callback_query(F.data == "back_to_support")
async def support(callback: types.CallbackQuery):
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)
    try:
        await callback.message.delete()
    except exceptions.TelegramBadRequest:
        pass

    _ru_back_to_support_text = (
        "<b>🛠 Служба поддержки</b>\n\n"
        "Мы ценим ваше доверие и всегда готовы помочь.\n"
        "Если у вас возникли сложности — обращайтесь напрямую. "
        "Мы ответим максимально быстро и с заботой о каждом пользователе.\n\n"
        "🔐 <b>Ваша безопасность</b> — наш главный приоритет.\n"
        "🎯 <b>Ваша уверенность</b> — наша ответственность.\n\n"
    )
    _uz_back_to_support_text = (
        "<b>🛠 Yordam xizmati</b>\n\n"
        "Biz doim aloqadamiz va yordam berishga tayyormiz.\n"
        "Agar muammo bo‘lsa — to‘g‘ridan-to‘g‘ri murojaat qiling.\n\n"
        "🔐 <b>Sizning xavfsizligingiz</b> — bizning ustuvor vazifamiz.\n"
        "🎯 <b>Sizning ishonchingiz</b> — bizning mas’uliyatimiz."
    )
    await callback.message.answer(
        _ru_back_to_support_text if user_lang == "ru" else _uz_back_to_support_text,
        parse_mode="HTML",
        reply_markup=user_inline.support(user_lang)
    )


@user_callback.callback_query(F.data.regexp(r"^buy_script:(.+)$"))
async def buy(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)

    if current_state == UserPaymentCheck.waiting_for_img:
        _ru_text_warning = "⛔ Сначала завершите текущую оплату — отправьте фото чека."
        _uz_text_warning = "⛔ Avval joriy to‘lovni yakunlang — chek fotosuratini yuboring."

        await callback.answer(
            _ru_text_warning if user_lang == "ru" else _uz_text_warning,
            show_alert=True
        )
        return
    # await callback.answer()
    try:
        await callback.message.delete()
    except exceptions.TelegramBadRequest:
        pass

    redis_key = callback.data.split("buy_script:")[1]
    raw_data = await redis.get(f"buy_script:{redis_key}")

    if not raw_data:
        return

    data = json.loads(raw_data)

    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=data.get("payment_msg_id"),
            reply_markup=None
        )
    except:
        pass

    if data.get("error_msg_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("error_msg_id")
            )
        except:
            pass

    if data.get("resend_msg_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("resend_msg_id")
            )
        except:
            pass

    if data.get("err_warning_message_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("err_warning_message_id")
            )
        except:
            pass

    referrals = await sync_to_async(operations.get_referrals_counts)(callback.from_user.id)
    referrals_list = referrals.get('unused', [])[:5]
    referrals_count = len(referrals_list)

    base_price = settings.SCRIPT_BASE_PRICE
    discount = referrals_count * settings.REWERD_PER_REFFERAL
    payment_sum = max(base_price - discount, 0)

    _ru_referral_note = (
        f"<s>{base_price} сум</s> → <b>{payment_sum} сум</b>\n"
        if referrals_count > 0 else
        f"<b>{payment_sum} сум</b>\n"
    )
    _uz_referral_note = (
        f"<s>{base_price} so‘m</s> → <b>{payment_sum} so‘m</b>\n"
        if referrals_count > 0 else
        f"<b>{payment_sum} so‘m</b>\n"
    )

    await state.set_state(UserPaymentCheck.waiting_for_img)
    await state.update_data(redis_key=redis_key)

    CARD_FOR_PAYMENT = settings.CARD_FOR_PAYMENT
    NAME_CARD = settings.NAME_CARD


    _ru_msg_payment = (
        f"💳 К оплате: {_ru_referral_note}\n"
        f"🆔 <code>{data.get('key')}</code>\n"
        f"⏱ <code>{data.get('start_at')}</code>\n"
        f"⏳ <code>{data.get('stop_at')}</code>\n\n"
        f"💰 <b>Карта для перевода:</b>\n<code>{CARD_FOR_PAYMENT}</code>\n"
        f"Владелец: <b>{NAME_CARD}</b>\n\n"
        "<b>📸 После оплаты просто пришли сюда фото или скриншот чека.</b>"
    )
    _uz_msg_payment = (
        f"💳 To‘lov summasi: {_uz_referral_note}\n"
        f"🆔 <code>{data.get('key')}</code>\n"
        f"⏱ <code>{data.get('start_at')}</code>\n"
        f"⏳ <code>{data.get('stop_at')}</code>\n\n"
        f"💰 <b>To‘lov uchun karta:</b>\n<code>{CARD_FOR_PAYMENT}</code>\n"
        f"Egasining ismi: <b>{NAME_CARD}</b>\n\n"
        "<b>📸 To‘lovdan so‘ng, chek yoki skrinshotni shu yerga yuboring.</b>"
    )
    msg = await callback.message.answer(
        _ru_msg_payment if user_lang == "ru" else _uz_msg_payment,
        parse_mode="HTML",
        reply_markup=user_inline.cancel_keyboard(redis_key, user_lang)
    )

    data["payment_msg_id"] = msg.message_id
    data["payment_sum"] = payment_sum
    data["referrals_count"] = referrals_list
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))


@user_callback.callback_query(F.data.regexp(r"^cancel_payment:(.+)$"))
async def cancel_payment(callback: types.CallbackQuery, state: FSMContext):
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)

    # current_state = await state.get_state()
    # if current_state == UserPaymentCheck.waiting_for_img:
    #     _ru_text_warning = "⛔ Сначала завершите текущую оплату — отправьте фото чека."
    #     _uz_text_warning = "⛔ Avval joriy to‘lovni yakunlang — chek fotosuratini yuboring."
    #
    #     await callback.answer(
    #         _ru_text_warning if user_lang == "ru" else _uz_text_warning,
    #         show_alert=True
    #     )
    #     return
    await callback.answer()
    await state.clear()
    redis_key = callback.data.split("cancel_payment:")[1]

    raw_data = await redis.get(f"buy_script:{redis_key}")
    if not raw_data:
        return

    data = json.loads(raw_data)

    for msg_key in ("payment_msg_id", "send_payment_msg_id"):
        msg_id = data.get(msg_key)
        if msg_id:
            try:
                await bot.delete_message(chat_id=data.get("user_id"), message_id=msg_id)
            except:
                pass

    try:
        await callback.message.delete()
    except:
        pass

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
            message_id=raw_data.get("err_message_id")
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

    try:
        await bot.delete_message(
            chat_id=raw_data.get("user_id"),
            message_id=raw_data.get("err_warning_message_id")
        )
    except:
        pass

    await state.clear()
    await redis.delete(f"buy_script:{redis_key}")

    await callback.message.answer("❌ <b>Оплата отменена</b>" if user_lang == "ru" else "❌ <b>Toʻlov bekor qilindi</b>", parse_mode="HTML")


@user_callback.callback_query(F.data.regexp(r"send_pay:(.+)$"))
async def send_pay(callback: types.CallbackQuery, state: FSMContext):
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)
    redis_key = callback.data.split("send_pay:")[1]

    current_state = await state.get_state()
    if current_state == UserPaymentCheck.waiting_for_img:
        _ru_text_warning = "⛔ Сначала завершите текущую оплату — отправьте фото чека."
        _uz_text_warning = "⛔ Avval joriy to‘lovni yakunlang — chek fotosuratini yuboring."

        await callback.answer(
            _ru_text_warning if user_lang == "ru" else _uz_text_warning,
            show_alert=True
        )
        return

    if not redis_key:
        await state.clear()
        return

    raw_data = await redis.get(f"buy_script:{redis_key}")

    if not raw_data:
        await state.clear()
        return

    data = json.loads(raw_data)

    if data.get("payment_msg_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("payment_msg_id")
            )
        except:
            pass

    referral_list = data.get("referrals_count")
    if referral_list:
        for ref in referral_list:
            await sync_to_async(operations.change_status_referral_by_id)(
                referral_id=ref.get("id"),
                status=False
            )

    admins = await sync_to_async(operations.get_admins)()

    _admins_dict = {}

    user_id = data.get('user_id')
    user_info = await bot.get_chat(user_id)
    username = "@" + str(user_info.username) if user_info.username else "скрыт"

    caption = (
        f"👤 <b>User ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>Ключ:</b> <code>{data.get('key')}</code>\n"
        f"💰 <b>Сумма:</b> {data.get('payment_sum')} сум\n"
        f"⏱ <b>Начало:</b> <code>{data.get('start_at')}</code>\n"
        f"⏳ <b>Конец:</b> <code>{data.get('stop_at')}</code>"
    )

    for admin in admins:
        admin_id = admin.get("user")
        message = await callback.bot.send_photo(
            chat_id=admin_id,
            photo=data.get("file_id"),
            caption=caption,
            reply_markup=admin_inline.check_payment(redis_key),
            parse_mode="HTML"
        )
        _admins_dict[str(admin_id)] = message.message_id

    data["admins"] = _admins_dict
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))

    try:
        await bot.edit_message_reply_markup(
            chat_id=callback.from_user.id,
            message_id=callback.message.message_id,
            reply_markup=None,
        )
    except:
        pass

    _ru_payment_sent_text = (
        "🔎 <b>Платёж отправлен на проверку</b>\n\n"
        "Пожалуйста, подождите — администратор проверит чек и подтвердит активацию."
    )
    _uz_payment_sent_text = (
        "🔎 <b>To‘lov tekshirish uchun yuborildi</b>\n\n"
        "Iltimos, kuting — administrator chekni tekshiradi va faollashtirishni tasdiqlaydi."
    )
    await callback.message.answer(
        _ru_payment_sent_text if user_lang == "ru" else _uz_payment_sent_text,
        parse_mode="HTML"
    )

@user_callback.callback_query(F.data.regexp(r"^resend_pay:(.+)$"))
async def recheck_pay(callback: types.CallbackQuery, state: FSMContext):
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)
    redis_key = callback.data.split("resend_pay:")[1]

    current_state = await state.get_state()
    if current_state == UserPaymentCheck.waiting_for_img:
        _ru_text_warning = "⛔ Сначала завершите текущую оплату — отправьте фото чека."
        _uz_text_warning = "⛔ Avval joriy to‘lovni yakunlang — chek fotosuratini yuboring."

        await callback.answer(
            _ru_text_warning if user_lang == "ru" else _uz_text_warning,
            show_alert=True
        )
        return

    await callback.answer()

    raw_data = await redis.get(f"buy_script:{redis_key}")
    if not raw_data:
        return

    data = json.loads(raw_data)

    if data.get("resend_msg_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("resend_msg_id")
            )
        except:
            pass

    if data.get("send_payment_msg_id"):
        try:
            await bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=data.get("send_payment_msg_id")
            )
        except:
            pass

    _ru_resend_msg_text = (
        "📤 <b>Вы можете отправить новый чек</b>\n\n"
        "Просто пришлите сюда новое фото или скриншот оплаты."
    )
    _uz_resend_msg_text = (
        "📤 <b>Yangi chek yuborishingiz mumkin</b>\n\n"
        "Shu yerga yangi foto yoki skrinshot yuboring."
    )

    resended_msg = await callback.message.answer(
        _ru_resend_msg_text if user_lang == "ru" else _uz_resend_msg_text,
        parse_mode="HTML",
        reply_markup=user_inline.cancel_keyboard(redis_key, user_lang),
        show_alert=True
    )

    data["resend_msg_id"] = resended_msg.message_id
    await redis.set(f"buy_script:{redis_key}", json.dumps(data))
    await state.update_data(redis_key=redis_key)
    await state.set_state(UserPaymentCheck.waiting_for_img)


@user_callback.callback_query(F.data == "accept_policy")
async def accept_policy_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_lang = await sync_to_async(operations.get_user_language)(user_id)

    await sync_to_async(operations.set_police)(user_id, True)

    await callback.message.delete()
    await callback.answer("✅ Политика принята" if user_lang == "ru" else "✅ Siyosat qabul qilindi", show_alert=True)


@user_callback.callback_query(F.data == "read_policy")
async def read_policy_handler(callback: types.CallbackQuery):
    await callback.answer()
    user_lang = await sync_to_async(operations.get_user_language)(callback.from_user.id)
    try:
        file = settings.POLICE_FILE_TG_ID_DOCUMENT_RU if user_lang == "ru" else settings.POLICE_FILE_TG_ID_DOCUMENT_UZ
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=file,
            caption="<b>📖 Политика использования</b>" if user_lang == "ru" else "<b>📖 Foydalanish siyosati</b>",
            parse_mode="HTML"
        )
    except:
        await callback.message.answer(
            text="<b>📖 Политика использования</b>" if user_lang == "ru" else "<b>📖 Foydalanish siyosati</b>",
            parse_mode="HTML"
        )


