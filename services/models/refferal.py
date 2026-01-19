from services.crypto import CompactReferralCipher
from django.conf import settings


def generate_referral_link(user_id: int) -> str:
    cipher = CompactReferralCipher()
    referral_code = cipher.encrypt_id(user_id)
    bot_username = settings.BOT_USERNAME
    return f"https://t.me/{bot_username}?start={referral_code}"
