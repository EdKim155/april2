#!/usr/bin/env python3
"""
Скрипт создания Telegram сессии для упрощенной автоматизации
Используется для первичной авторизации в Telegram
"""
import asyncio
import logging
from telethon import TelegramClient

# ============================================================================
# КОНФИГУРАЦИЯ - НОВЫЕ CREDENTIALS
# ============================================================================
API_ID = 24101164
API_HASH = '80cc2adcd452008ae630d0ee778b5122'
PHONE_NUMBER = '+79512586335'
SESSION_NAME = 'simple_automation_session'

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def create_session():
    """Создание новой Telegram сессии"""

    print("=" * 70)
    print("🔐 СОЗДАНИЕ TELEGRAM СЕССИИ")
    print("=" * 70)
    print(f"📱 Номер телефона: {PHONE_NUMBER}")
    print(f"📝 Имя сессии: {SESSION_NAME}.session")
    print("=" * 70)
    print()

    # Создаем клиент
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        print("🔄 Подключение к Telegram...")
        await client.connect()

        if not await client.is_user_authorized():
            print("📲 Отправка кода авторизации на номер...")
            await client.send_code_request(PHONE_NUMBER)

            print()
            print("─" * 70)
            code = input("✏️  Введите код из Telegram: ")
            print("─" * 70)
            print()

            try:
                await client.sign_in(PHONE_NUMBER, code)
            except Exception as e:
                if "Two-steps verification" in str(e) or "password" in str(e).lower():
                    print("🔒 Обнаружена двухфакторная аутентификация")
                    print("─" * 70)
                    password = input("✏️  Введите пароль 2FA: ")
                    print("─" * 70)
                    print()
                    await client.sign_in(password=password)
                else:
                    raise

        # Проверяем авторизацию
        me = await client.get_me()

        print("=" * 70)
        print("✅ АВТОРИЗАЦИЯ УСПЕШНА!")
        print("=" * 70)
        print(f"👤 Пользователь: {me.first_name} {me.last_name or ''}")
        print(f"🆔 ID: {me.id}")
        print(f"📱 Телефон: {me.phone}")
        print(f"📁 Файл сессии: {SESSION_NAME}.session")
        print("=" * 70)
        print()
        print("🎉 Сессия создана и сохранена!")
        print("Теперь можете запускать ./simple_start.sh")
        print("=" * 70)

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ОШИБКА ПРИ СОЗДАНИИ СЕССИИ")
        print("=" * 70)
        print(f"Ошибка: {e}")
        print("=" * 70)
        raise

    finally:
        await client.disconnect()


if __name__ == '__main__':
    try:
        asyncio.run(create_session())
    except KeyboardInterrupt:
        print("\n\n❌ Отменено пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
