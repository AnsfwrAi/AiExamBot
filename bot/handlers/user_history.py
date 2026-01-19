from datetime import datetime
from aiogram import Router, F, types
from asgiref.sync import sync_to_async
from django.conf import settings
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import State, StatesGroup
from aiogram.exceptions import TelegramBadRequest
import math

from .. import CommandMap
from .. import bot, redis
from ..keyboards.history import inline as inline_history

from services.models import operations

user_history = Router()


def parse_dt(val: str):
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return val


class HistoreState(StatesGroup):
    button = State()
    page = State()
    scripts = State()
    detail = State()


def format_scripts_text(scripts: list) -> str:
    text = "<b>Ваши покупки:</b>\n\n"
    for s in scripts:
        start = parse_dt(s["start_at"])
        stop = parse_dt(s["stop_at"])
        text += (
            f"🆔 <code>{s['key']}</code>\n"
            f"📜 {s['script']}\n"
            f"⏱ {start} - {stop}\n"
            f"{'💰 Оплачено' if s['is_active'] else '🚫 Не оплачено'}\n"
            f"_____________\n\n"
        )
    return text


def format_script_detail(script: dict) -> str:
    start = parse_dt(script["start_at"])
    stop = parse_dt(script["stop_at"])

    detail_text = (
        f"<b>📋 Детали сессии</b>\n\n"
        f"🆔 <b>Ключ:</b> <code>{script['key']}</code>\n"
        f"📜 <b>Скрипт:</b> {script['script']}\n"
        f"⏱ <b>Начало:</b> {start}\n"
        f"⏱ <b>Конец:</b> {stop}\n"
        f"📊 <b>Статус:</b> {'✅ Оплачено и активно' if script['is_active'] else '❌ Не оплачено'}\n"
    )

    if script['is_active']:
        detail_text += f"\n🔗 <b>Ссылка на решение:</b>\njavascript:import('{settings.GET_SCRIPT_JS}/{script['script']}')\n"
        detail_text += f"\n💡 <b>Как использовать:</b>\nПерейдите по ссылке в указанное время работы скрипта."

        if not script.get('fingerprint'):
            detail_text += f"\n\n🕐 <b>Изменение времени:</b>\nВы можете изменить время работы скрипта до его первого использования."
        else:
            detail_text += f"\n\n🔒 <b>Время заблокировано:</b>\nСкрипт уже был использован, время изменить нельзя."
    else:
        detail_text += f"\n⚠️ <b>Внимание:</b> Скрипт не активен. Возможно, платеж не был подтвержден."

    return detail_text


def get_detail_keyboard(script: dict):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    buttons = []

    if script['is_active'] and not script.get('fingerprint'):
        buttons.append([
            InlineKeyboardButton(
                text="🕐 Изменить время",
                web_app={"url": f"{settings.WEB_APP_REDACT_TIME_URL}?key={script['key']}"}
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔙 Назад к списку",
            callback_data="back_to_scripts_list"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_back_to_list_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_scripts_list"
                )
            ]
        ]
    )


async def render_sessions_page(message: types.Message, scripts: list, page: int):
    per_page = 5
    total_pages = math.ceil(len(scripts) / per_page)
    start_idx = page * per_page
    end_idx = start_idx + per_page

    current = scripts[start_idx:end_idx]
    text = format_scripts_text(current)

    await message.answer(
        text,
        reply_markup=inline_history.get_page_keyboard_sessions_history(page + 1, total_pages, current),
        parse_mode="HTML"
    )


@user_history.message(F.text.in_([CommandMap.User.Ru.MY_SCRIPTS, CommandMap.User.Uz.MY_SCRIPTS]))
async def my_sessions_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    await state.clear()
    await state.set_state(HistoreState.button)

    my_scripts = await sync_to_async(operations.get_my_scripts)(message.from_user.id)
    if not my_scripts:
        await message.answer("❗️ У вас нет активных сессий")
        return

    await state.update_data(scripts=my_scripts, page=0)
    await render_sessions_page(message, my_scripts, 0)


@user_history.callback_query(F.data.startswith("scripts_page_"))
async def handle_scripts_page(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state not in [HistoreState.button, HistoreState.detail]:
        await callback.answer("⚠️ Сессия истекла", show_alert=True)
        return

    data = await state.get_data()
    scripts = data.get("scripts", [])

    if not scripts:
        await callback.answer("❌ Нет данных")
        return

    try:
        page = int(callback.data.split("_")[-1]) - 1
    except (ValueError, IndexError):
        await callback.answer("❌ Неверный формат страницы")
        return

    per_page = 5
    total_pages = math.ceil(len(scripts) / per_page)

    if page < 0 or page >= total_pages:
        await callback.answer("❌ Неверная страница")
        return

    await state.set_state(HistoreState.button)
    await state.update_data(page=page)

    start_idx = page * per_page
    end_idx = start_idx + per_page
    current = scripts[start_idx:end_idx]

    text = format_scripts_text(current)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=inline_history.get_page_keyboard_sessions_history(page + 1, total_pages, current),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны")
        else:
            raise

    await callback.answer()


@user_history.callback_query(F.data.startswith("script_detail_"))
async def script_detail(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != HistoreState.button:
        await callback.answer("⚠️ Сессия истекла", show_alert=True)
        return

    try:
        script_id = int(callback.data.split("_")[-1])
    except (ValueError, IndexError):
        await callback.answer("❌ Неверный ID скрипта")
        return

    data = await state.get_data()
    scripts = data.get("scripts", [])

    script = next((s for s in scripts if s.get('id') == script_id), None)
    if not script:
        await callback.answer("❌ Скрипт не найден")
        return

    await state.update_data(current_script=script)
    await state.set_state(HistoreState.detail)

    detail_text = format_script_detail(script)

    try:
        await callback.message.edit_text(
            detail_text,
            reply_markup=get_detail_keyboard(script),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны")
        else:
            raise

    await callback.answer()


@user_history.callback_query(F.data == "back_to_scripts_list")
async def back_to_scripts_list(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != HistoreState.detail:
        await callback.answer("⚠️ Неверное состояние", show_alert=True)
        return

    await state.set_state(HistoreState.button)

    data = await state.get_data()
    scripts = data.get("scripts", [])
    page = data.get("page", 0)

    if not scripts:
        await callback.message.edit_text("❗️ У вас нет активных сессий")
        await state.clear()
        return

    per_page = 5
    total_pages = math.ceil(len(scripts) / per_page)
    start_idx = page * per_page
    end_idx = start_idx + per_page
    current = scripts[start_idx:end_idx]

    text = format_scripts_text(current)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=inline_history.get_page_keyboard_sessions_history(page + 1, total_pages, current),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны")
        else:
            raise

    await callback.answer()


@user_history.callback_query(F.data == "refresh_script_time")
async def refresh_script_time(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state != HistoreState.detail:
        await callback.answer("⚠️ Сессия истекла", show_alert=True)
        return

    data = await state.get_data()
    current_script = data.get("current_script")

    if not current_script:
        await callback.answer("❌ Данные скрипта не найдены")
        return

    script_key = current_script['key']
    updated_script = await sync_to_async(operations.get_script_by_key)(script_key)

    if not updated_script:
        await callback.answer("❌ Скрипт не найден в базе данных")
        return

    scripts = data.get("scripts", [])
    for i, script in enumerate(scripts):
        if script['key'] == script_key:
            scripts[i] = updated_script
            break

    await state.update_data(scripts=scripts, current_script=updated_script)

    detail_text = format_script_detail(updated_script)

    try:
        await callback.message.edit_text(
            detail_text,
            reply_markup=get_detail_keyboard(updated_script),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны")
        else:
            raise

    await callback.answer("🔄 Время обновлено!")


@user_history.callback_query(F.data == "scripts_page_1")
async def refresh_scripts(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state not in [HistoreState.button, HistoreState.detail]:
        await callback.answer("⚠️ Сессия истекла", show_alert=True)
        return

    my_scripts = await sync_to_async(operations.get_my_scripts)(callback.from_user.id)
    if not my_scripts:
        await callback.message.edit_text("❗️ У вас нет активных сессий")
        await state.clear()
        return

    await state.set_state(HistoreState.button)
    await state.update_data(scripts=my_scripts, page=0)

    per_page = 5
    total_pages = math.ceil(len(my_scripts) / per_page)
    current = my_scripts[:per_page]
    text = format_scripts_text(current)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=inline_history.get_page_keyboard_sessions_history(1, total_pages, current),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer("Данные актуальны")
        else:
            raise

    await callback.answer("🔄 Обновлено")


@user_history.callback_query(F.data == "current_page")
async def current_page_info(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    page = data.get("page", 0)
    scripts = data.get("scripts", [])
    total_pages = math.ceil(len(scripts) / 5) if scripts else 1

    await callback.answer(f"📄 Страница {page + 1} из {total_pages}")