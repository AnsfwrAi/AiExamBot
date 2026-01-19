from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio

from bot.runner import bot

class Command(BaseCommand):
    help = "Sets the Telegram bot webhook"

    def handle(self, *args, **kwargs):
        webhook_url = f"{settings.WEBHOOK_URL}"
        self.stdout.write(self.style.NOTICE(f"📡 Setting webhook to: {webhook_url}"))

        asyncio.run(self.set_webhook(webhook_url))

    async def set_webhook(self, url):
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            await bot.set_webhook(
                url=url,
                allowed_updates=["message", "callback_query"],
            )
            print(f"✅ Webhook successfully set to: {url}")
        finally:
            await bot.session.close()
