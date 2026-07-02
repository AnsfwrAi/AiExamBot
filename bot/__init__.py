from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings
from redis.asyncio import Redis
import os

bot = Bot(token=settings.BOT_TOKEN)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis = Redis(host=redis_host, port=redis_port, decode_responses=True)


class CommandMap:
    class User:
        class Ru:
            BUY_SCRIPT = "💰Купить решение"
            MY_SCRIPTS = "📦 Покупки"
            MY_DATA = "👥 Рефералы"
            INSTRUCTION = "📄 Инструкции"
            SUPPORT = "🛠 Поддержка"
            LANGUAGE = "🌐 Язык"

        class Uz:
            BUY_SCRIPT = "💰Yechim sotib olish"
            MY_SCRIPTS = "📦 Xaridlar"
            MY_DATA = "👥 Referallar"
            INSTRUCTION = "📄 Ko'rsatmalar"
            SUPPORT = "🛠 Qo'llab-quvvatlash"
            LANGUAGE = "🌐 Til"

    class Admin:
        DEV_MENU = "Dev_menu"
        BUY_SCRIPT = "💰Купить решение"
        MY_SCRIPTS = "📦 Покупки"
        MY_DATA = "👥 Рефералы"
        INSTRUCTION = "📄 Инструкции"
        SUPPORT = "🛠 Поддержка"

