import asyncio
import json

from aiogram.fsm.context import FSMContext
import html
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from asgiref.sync import sync_to_async

from bot import CommandMap
from services.models import operations
from .. import bot
from ..keyboards.admin import inline

admin = Router()

class DevStates(StatesGroup):
    waiting_for_media = State()
    waiting_for_file_id = State()
    waiting_for_file_type = State()

@admin.message(Command("admin_panel"))
async def admin_panel(message: Message):
    user_id = message.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    await message.answer("Admin panel")


@admin.message(F.text == CommandMap.Admin.DEV_MENU)
async def dev_menu(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    await message.answer("🛠 <b>Developer Menu</b>", reply_markup=inline.dev_menu(), parse_mode="HTML")

@admin.callback_query(F.data == "metadata_file")
async def ask_for_media(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    await callback.message.answer("📤 Пришли любой медиафайл (документ, фото, видео, аудио, стикер и т.д.)")
    await state.set_state(DevStates.waiting_for_media)
    await callback.answer()


@admin.message(DevStates.waiting_for_media)
async def handle_any_media(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    metadata = []
    if message.photo:
        for i, p in enumerate(message.photo):
            meta = {}
            for attr in dir(p):
                if not attr.startswith("_") and not callable(getattr(p, attr)):
                    try:
                        meta[attr] = str(getattr(p, attr))
                    except Exception:
                        meta[attr] = "⚠️ ERROR"
            metadata.append({f"photo_variant_{i}": meta})

    else:
        media_obj = (
            message.document or message.video or message.audio or message.voice or
            message.sticker or message.animation or message.video_note
        )

        if not media_obj:
            await message.answer("⛔️ Не могу обработать это сообщение. Пришли медиафайл.")
            return

        meta = {}
        for attr in dir(media_obj):
            if not attr.startswith("_") and not callable(getattr(media_obj, attr)):
                try:
                    meta[attr] = str(getattr(media_obj, attr))
                except Exception:
                    meta[attr] = "⚠️ ERROR"
        metadata = meta

    await message.answer(
        f"<b>📎 Метаданные:</b>\n<pre>{json.dumps(metadata, indent=2, ensure_ascii=False)}</pre>",
        parse_mode="HTML"
    )
    await state.clear()


@admin.callback_query(F.data == "get_file_by_id")
async def ask_file_id(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    await callback.message.answer("📎 Введи <code>file_id</code> (можно скопировать из метаданных)", parse_mode="HTML")
    await state.set_state(DevStates.waiting_for_file_id)
    await callback.answer()

@admin.message(DevStates.waiting_for_file_id)
async def store_file_id_and_ask_type(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    await state.update_data(file_id=message.text.strip())
    await message.answer(
        "🔍 Укажи тип файла, чтобы я знал, как отправить:\n"
        "<b>document</b>, <b>photo</b>, <b>video</b>, <b>audio</b>, <b>voice</b>, <b>animation</b>, <b>sticker</b>",
        parse_mode="HTML"
    )
    await state.set_state(DevStates.waiting_for_file_type)


@admin.message(DevStates.waiting_for_file_type)
async def handle_file_type_and_send(message: types.Message, state: FSMContext, bot):
    user_id = message.from_user.id
    if not await sync_to_async(operations.check_admin)(user_id):
        return
    data = await state.get_data()
    file_id = data.get("file_id")
    file_type = message.text.strip().lower()

    try:
        if file_type == "document":
            await bot.send_document(message.chat.id, file_id)
        elif file_type == "photo":
            await bot.send_photo(message.chat.id, file_id)
        elif file_type == "video":
            await bot.send_video(message.chat.id, file_id)
        elif file_type == "audio":
            await bot.send_audio(message.chat.id, file_id)
        elif file_type == "voice":
            await bot.send_voice(message.chat.id, file_id)
        elif file_type == "animation":
            await bot.send_animation(message.chat.id, file_id)
        elif file_type == "sticker":
            await bot.send_sticker(message.chat.id, file_id)
        else:
            await message.answer("⛔ Неподдерживаемый тип файла.")
            return

        await message.answer("✅ Файл отправлен.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: <code>{html.escape(str(e))}</code>", parse_mode="HTML")

    await state.clear()



