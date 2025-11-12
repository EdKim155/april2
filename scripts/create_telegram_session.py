#!/usr/bin/env python3
"""
Утилита для создания новой Telegram-сессии.
По умолчанию использует предоставленные API_ID, API_HASH и номер телефона,
но их можно переопределить через переменные окружения:

    export API_ID=123456
    export API_HASH="abcd1234"
    export PHONE_NUMBER="+79998887766"
    export SESSION_NAME="custom_session"
"""

import asyncio
import os
from telethon import TelegramClient


def _env(key: str, default: str) -> str:
    """Возвращает значение переменной окружения с запасным вариантом."""
    return os.getenv(key, default)


API_ID = int(_env("API_ID", "24101164"))
API_HASH = _env("API_HASH", "80cc2adcd452008ae630d0ee778b5122")
PHONE_NUMBER = _env("PHONE_NUMBER", "+79512586335")
SESSION_NAME = _env("SESSION_NAME", "telegram_session")


async def create_session() -> None:
    """Создает новую сессию и сохраняет ее в файл SESSION_NAME.session."""
    print("=" * 60)
    print("🔐 Создание Telegram-сессии")
    print("=" * 60)
    print(f"API_ID: {API_ID}")
    print(f"API_HASH: {API_HASH}")
    print(f"PHONE_NUMBER: {PHONE_NUMBER}")
    print(f"SESSION_NAME: {SESSION_NAME}")
    print("=" * 60)
    print("➡️  Ожидайте SMS или звонок с кодом подтверждения.")
    print("➡️  Введите код, когда Telethon запросит его в консоли.")
    print("➡️  Если включен пароль 2FA, клиент запросит его дополнительно.")

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.start(phone=PHONE_NUMBER)
        me = await client.get_me()
        print("\n✅ Сессия успешно сохранена.")
        print(f"📁 Файл: {SESSION_NAME}.session")
        print("\n👤 Аккаунт:")
        print(f"   Имя: {me.first_name} {me.last_name or ''}".strip())
        username = f"@{me.username}" if me.username else "не задан"
        print(f"   Username: {username}")
        print(f"   ID: {me.id}")
    except Exception as exc:
        print("\n❌ Не удалось создать сессию.")
        print(f"Причина: {exc}")
        print("\nПроверьте корректность API_ID/API_HASH, номера телефона и доступ к Telegram.")
        raise
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(create_session())
