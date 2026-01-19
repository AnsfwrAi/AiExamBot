from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from django.conf import settings
from redis.asyncio import Redis

bot = Bot(token=settings.BOT_TOKEN)
storage = RedisStorage.from_url(settings.REDIS_URL)
dp = Dispatcher(storage=storage)
redis = Redis(host="localhost", port=6379, decode_responses=True)


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

