import hashlib
import base64
import json
import urllib.parse
import hmac
from cryptography.fernet import Fernet
import time
from django.conf import settings



SECRET_KEY = settings.SECRET_KEY

class SimpleCipher:
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            if SECRET_KEY is None:
                raise ValueError("SECRET_KEY is required. Either pass it explicitly or configure Django settings.")
            secret_key = SECRET_KEY

        key = hashlib.sha256(secret_key.encode()).digest()
        self.key = base64.urlsafe_b64encode(key)
        self.cipher = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def encrypt_for_url(self, plaintext: str) -> str:
        token = self.encrypt(plaintext)
        return urllib.parse.quote(token)

    def decrypt(self, token: str) -> str:
        token = urllib.parse.unquote(token)
        return self.cipher.decrypt(token.encode()).decode()

class CompactReferralCipher:
    def __init__(self, secret_key: str = None):
        if secret_key is None:
            if SECRET_KEY is None:
                raise ValueError("SECRET_KEY is required.")
            secret_key = SECRET_KEY
        self.secret_key = secret_key.encode()

    def encrypt_id(self, user_id: int) -> str:
        id_bytes = str(user_id).encode()
        signature = hmac.new(self.secret_key, id_bytes, hashlib.sha256).digest()[:4]
        token = base64.urlsafe_b64encode(id_bytes + signature).decode().rstrip("=")
        return token

    def decrypt_id(self, token: str) -> int | None:
        try:
            padded = token + "=" * (-len(token) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            user_id_bytes, signature = decoded[:-4], decoded[-4:]
            expected = hmac.new(self.secret_key, user_id_bytes, hashlib.sha256).digest()[:4]
            if hmac.compare_digest(signature, expected):
                return int(user_id_bytes.decode())
        except Exception:
            pass
        return None


import hashlib
import hmac
from urllib.parse import unquote
from typing import Tuple, List


class TelegramWebAppValidator:

    @staticmethod
    def is_safe(bot_token: str, init_data: str) -> bool:
        """
        Проверяет, что initData действительно от Telegram.

        Args:
            bot_token: токен вашего бота
            init_data: данные инициализации от Telegram (Telegram.WebApp.initData)

        Returns:
            True если данные от Telegram, иначе False
        """
        checksum, sorted_init_data = TelegramWebAppValidator._convert_init_data(init_data)

        secret_key = hmac.new(
            key=b'WebAppData',
            msg=bot_token.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()

        hash_value = hmac.new(
            key=secret_key,
            msg=sorted_init_data.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()

        return hash_value == checksum

    @staticmethod
    def _convert_init_data(init_data: str) -> Tuple[str, str]:
        """
        Конвертирует init data в формат key=value и сортирует по алфавиту.

        Args:
            init_data: данные инициализации от Telegram

        Returns:
            Кортеж (hash, sorted_init_data)
        """
        # Декодируем URL-encoded данные
        decoded_data = unquote(init_data)
        init_data_array = decoded_data.split('&')

        needle = 'hash='
        hash_value = ''
        filtered_data = []

        for data in init_data_array:
            if data.startswith(needle):
                hash_value = data[len(needle):]
            else:
                filtered_data.append(data)

        filtered_data.sort()

        sorted_init_data = '\n'.join(filtered_data)

        return hash_value, sorted_init_data


if __name__ == "__main__":
    bot_token = "YOUR_BOT_TOKEN"
    init_data = "query_id=AAHdF6IQAAAAAN0XohAAABCy&user=%7B%22id%22%3A279058397%22%7D&hash=b25f9c..."

    validator = TelegramWebAppValidator()
    if validator.is_safe(bot_token, init_data):
        print("✅ Данные безопасны - от Telegram")
    else:
        print("❌ Данные небезопасны - НЕ от Telegram")