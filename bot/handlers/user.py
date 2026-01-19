import json

from aiogram import F, types, Router, exceptions
from asgiref.sync import sync_to_async
from django.conf import settings
from aiogram.fsm.context import FSMContext

from ..keyboards.user import inline as user_inline, reply as user_reply
from ..keyboards.admin import inline as admin_inline, reply as admin_reply
from .. import CommandMap, redis
from ..fsm.user import UserPaymentCheck
from ..filters import police
from .. import bot

from services.models import operations
from services.models import refferal


user = Router()

@user.message(F.text.in_([CommandMap.User.Ru.BUY_SCRIPT, CommandMap.User.Uz.BUY_SCRIPT]), police.HasAcceptedPolicy())
async def buy_script(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    __user = await sync_to_async(operations.get_or_create_tg_user)(message.from_user.id)
    user_language = __user.get("language", "ru")

    if state_name == UserPaymentCheck.waiting_for_img:
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
            _ru_dont_image if user_language == "ru" else _uz_dont_image,
            parse_mode="HTML",
            reply_markup=user_inline.cancel_keyboard(redis_key=redis_key,
                         user_language=user_language) if redis_key else None
        )

        data["error_msg_id"] = err_dont_image_message.message_id
        await redis.set(f"buy_script:{redis_key}", json.dumps(data))
        return

    _ru_buy_script_text_form = ("<b>💼 Покупка решения — быстро и надёжно</b>\n\n"
                                "<b>1️⃣ Выберите дату и время теста</b>\n"
                                "Укажите заранее, чтобы мы всё подготовили.\n\n"
                                "<b>2️⃣ Оплатите заказ</b>\n"
                                "Мы принимаем оплату и сразу начинаем работу.\n\n"
                                "<b>3️⃣ Получите решение через AFT</b>\n"
                                "Точно в нужное время, без задержек.\n\n"
                                "<b>🔐 Мы гарантируем:</b>\n"
                                "– Полную конфиденциальность\n"
                                "– Своевременную отправку\n"
                                "– Рабочее и проверенное решение")

    _uz_buy_script_text_form = ("<b>💼 Yechimni xarid qilish — tez va ishonchli</b>\n\n"
                                "<b>1️⃣ Test sanasi va vaqtini tanlang</b>\n"
                                "Oldindan belgilang, biz hammasini tayyorlab qo‘yamiz.\n\n"
                                "<b>2️⃣ Buyurtmani to‘lang</b>\n"
                                "To‘lovni qabul qilamiz va darhol ishni boshlaymiz.\n\n"
                                "<b>3️⃣ AFT orqali yechimni oling</b>\n"
                                "Aynan kerakli vaqtda, kechikishsiz.\n\n"
                                "<b>🔐 Biz kafolatlaymiz:</b>\n"
                                "– To‘liq maxfiylik\n"
                                "– O‘z vaqtida yuborish\n"
                                "– Ishlaydigan va tekshirilgan yechim")

    await message.answer(
        _ru_buy_script_text_form if user_language == "ru" else _uz_buy_script_text_form,
        reply_markup=user_inline.select_time(user_language),
        parse_mode="HTML"
    )


@user.message(F.text.in_([CommandMap.User.Ru.MY_DATA, CommandMap.User.Uz.MY_DATA]), police.HasAcceptedPolicy())
async def my_referrals(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    __user = await sync_to_async(operations.get_or_create_tg_user)(message.from_user.id)
    user_language = __user.get("language", "ru")

    if state_name == UserPaymentCheck.waiting_for_img:
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
            _ru_dont_image if user_language == "ru" else _uz_dont_image,
            parse_mode="HTML",
            reply_markup=user_inline.cancel_keyboard(redis_key=redis_key,
                         user_language=user_language) if redis_key else None
        )

        data["error_msg_id"] = err_dont_image_message.message_id
        await redis.set(f"buy_script:{redis_key}", json.dumps(data))
        return

    user_id = message.from_user.id

    referral_link = await sync_to_async(refferal.generate_referral_link)(user_id)
    referral_buys = await sync_to_async(operations.get_referrals_counts)(user_id)
    invited_users = await sync_to_async(operations.get_referrals_inviters)(user_id)

    reward_per_referral = settings.REWERD_PER_REFFERAL
    max_discount = settings.MAX_DISCOUNT

    successful_referrals = len(referral_buys["all"])
    unused_referrals = len(referral_buys["unused"])
    total_discount = unused_referrals * reward_per_referral

    _ru_referral_title = (
        "<b>👥 Реферальная программа</b>\n\n"
        "💸 <b>За каждого человека</b>, который совершит покупку по вашей ссылке, вы получаете "
        f"<b>скидку {reward_per_referral:,} сум</b>.\n"
        f"🔐 <b>Максимальная скидка</b> на одну покупку — <b>{max_discount:,} сум</b>.\n\n"
        "📌 <b>Ваша реферальная ссылка:</b>\n"
        f"{referral_link}\n\n"
        "📊 <b>Статистика</b>:\n"
        f"— Приглашено: <b>{len(invited_users)} человек</b>\n"
        f"- Совершили покупку: <b>{successful_referrals} покупок</b>\n"
        f"— Доступная скидка: <b>{unused_referrals} / {total_discount:,} сум</b>"
    )
    _uz_referral_title = (
        "<b>👥 Referal dasturi</b>\n\n"
        "💸 <b>Sizning havolangiz orqali</b> xarid qilgan har bir foydalanuvchi uchun "
        f"<b>{reward_per_referral:,} so‘m chegirma</b> olasiz.\n"
        f"🔐 <b>Bitta xarid uchun maksimal chegirma</b> — <b>{max_discount:,} so‘m</b>.\n\n"
        "📌 <b>Sizning referal havolangiz:</b>\n"
        f"{referral_link}\n\n"
        "📊 <b>Statistika</b>:\n"
        f"— Taklif qilinganlar: <b>{len(invited_users)} kishi</b>\n"
        f"— Xarid qilganlar: <b>{successful_referrals} ta xarid</b>\n"
        f"— Mavjud chegirma: <b>{unused_referrals} / {total_discount:,} so‘m</b>"
    )

    await message.answer(
        _ru_referral_title if user_language == "ru" else _uz_referral_title,
        parse_mode="HTML"
    )



@user.message(F.text.in_([CommandMap.User.Ru.INSTRUCTION, CommandMap.User.Uz.INSTRUCTION]), police.HasAcceptedPolicy())
async def instruction(message: types.Message, state: FSMContext):
    __user = await sync_to_async(operations.get_or_create_tg_user)(message.from_user.id)
    user_language = __user.get("language", "ru")
    state_name = await state.get_state()

    if state_name == UserPaymentCheck.waiting_for_img:
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
            _ru_dont_image if user_language == "ru" else _uz_dont_image,
            parse_mode="HTML",
            reply_markup=user_inline.cancel_keyboard(redis_key=redis_key,
                         user_language=user_language) if redis_key else None
        )

        data["error_msg_id"] = err_dont_image_message.message_id
        await redis.set(f"buy_script:{redis_key}", json.dumps(data))
        return

    _ru_common_instruction = (
        f"📌 <b>Инструкция по запуску скрипта</b>\n\n"
        f"🔹 <b>Что это?</b>\n"
        f"Ты получил персональную ссылку, которая позволяет активировать вспомогательный интерфейс прямо в браузере:\n"
        f"<code>javascript:import('//aft.ink/&lt;твой_код&gt;')</code>\n\n"

        f"🔧 <b>Как использовать:</b>\n"
        f"1. Открой любой веб-сайт, с которым ты сейчас работаешь\n"
        f"2. Убедись, что страница полностью загрузилась\n"
        f"3. Скопируй выданную ссылку и вставь её в адресную строку браузера (не в поисковик!)\n"
        f"4. Нажми Enter — система активирует необходимый функционал\n\n"

        f"⚙️ <b>Требования:</b>\n"
        f"• Современный браузер (Chrome, Firefox, Edge на ПК)\n"
        f"• Скрипт не работает на мобильных устройствах и в Safari\n"

        f"❓ <b>Если возникли вопросы:</b>\n"
        f"• Проверь, что вставляешь ссылку без пробелов и лишних символов\n"
        f"• Обнови страницу и попробуй ещё раз\n\n"

        f"📬 <b>Поддержка:</b> <a href='https://t.me/AFT_Admin1'>@AFT_Admin1</a>\n\n"
        f"<i>Инструкция предоставлена для активации вспомогательного интерфейсного решения.</i>"
    )

    _uz_common_instruction = (
        f"📌 <b>Skriptni ishga tushirish bo‘yicha yo‘riqnoma</b>\n\n"
        f"🔹 <b>Bu nima?</b>\n"
        f"Siz brauzerda to‘g‘ridan-to‘g‘ri yordamchi interfeysni faollashtirish imkonini beruvchi shaxsiy havolani oldingiz:\n"
        f"<code>javascript:import('//aft.ink/&lt;your_code&gt;')</code>\n\n"

        f"🔧 <b>Qanday foydalaniladi:</b>\n"
        f"1. Hozir ishlayotgan istalgan veb-saytni oching\n"
        f"2. Sahifa to‘liq yuklanganiga ishonch hosil qiling\n"
        f"3. Berilgan havolani nusxalab, brauzer manzil satriga joylashtiring (qidiruvga emas!)\n"
        f"4. Enter tugmasini bosing — tizim kerakli funksiyalarni faollashtiradi\n\n"

        f"⚙️ <b>Talablar:</b>\n"
        f"• Zamonaviy brauzer (Chrome, Firefox, Edge — ПК uchun)\n"
        f"• Skript mobil qurilmalarda va Safari brauzerida ishlamaydi\n"

        f"❓ <b>Agar savollar bo‘lsa:</b>\n"
        f"• Havolani bo‘shliqlarsiz va ortiqcha belgilarisiz joylashtirayotganingizni tekshiring\n"
        f"• Sahifani yangilang va yana urinib ko‘ring\n\n"

        f"📬 <b>Qo‘llab-quvvatlash:</b> <a href='https://t.me/AFT_Admin1'>@AFT_Admin1</a>\n\n"
        f"<i>Ushbu yo‘riqnoma yordamchi interfeys yechimini faollashtirish uchun taqdim etilgan.</i>"
    )

    try:
        vid = settings.VIDEO_INSTRUCTION_TG_ID_VIDEO_RU if user_language == "ru" else settings.VIDEO_INSTRUCTION_TG_ID_VIDEO_UZ
        await bot.send_video(
            chat_id=message.from_user.id,
            video=vid,
            caption=_ru_common_instruction if user_language == "ru" else _uz_common_instruction,
            parse_mode="HTML"
        )
    except exceptions.TelegramBadRequest as e:
        await bot.send_message(
            chat_id=message.from_user.id,
            text=_ru_common_instruction if user_language == "ru" else _uz_common_instruction,
            parse_mode="HTML"
        )
        

@user.message(F.text.in_([CommandMap.User.Ru.SUPPORT, CommandMap.User.Uz.SUPPORT]), police.HasAcceptedPolicy())
async def support(message: types.Message, state: FSMContext):
    state_name = await state.get_state()
    __user = await sync_to_async(operations.get_or_create_tg_user)(message.from_user.id)
    user_language = __user.get("language", "ru")
    if state_name == UserPaymentCheck.waiting_for_img:
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
            _ru_dont_image if user_language == "ru" else _uz_dont_image,
            parse_mode="HTML",
            reply_markup=user_inline.cancel_keyboard(redis_key=redis_key,
                                                     user_language=user_language) if redis_key else None
        )

        data["error_msg_id"] = err_dont_image_message.message_id
        await redis.set(f"buy_script:{redis_key}", json.dumps(data))
        return

    _ru_support_text = (
        "<b>🛠 Служба поддержки</b>\n\n"
        "Мы ценим ваше доверие и всегда готовы помочь.\n"
        "Если у вас возникли сложности — обращайтесь напрямую. "
        "Мы ответим максимально быстро и с заботой о каждом пользователе.\n\n"
        "🔐 <b>Ваша безопасность</b> — наш главный приоритет.\n"
        "🎯 <b>Ваша уверенность</b> — наша ответственность.\n\n"
    )

    _uz_support_text = (
        "<b>🛠 Qo‘llab-quvvatlash xizmati</b>\n\n"
        "Biz ishonchingizni qadrlaymiz va har doim yordam berishga tayyormiz.\n"
        "Agar qiyinchiliklar yuzaga kelsa — to‘g‘ridan-to‘g‘ri murojaat qiling. "
        "Biz imkon qadar tez va har bir foydalanuvchiga e’tibor bilan javob beramiz.\n\n"
        "🔐 <b>Sizning xavfsizligingiz</b> — bizning asosiy ustuvorligimiz.\n"
        "🎯 <b>Sizning ishonchingiz</b> — bizning mas’uliyatimiz.\n\n"
    )

    await message.answer(
        _ru_support_text if user_language == "ru" else _uz_support_text,
        parse_mode="HTML",
        reply_markup=user_inline.support(user_language)
    )

