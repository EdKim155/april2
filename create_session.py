#!/usr/bin/env python3
"""
Скрипт для создания Telegram сессии
Используется для первичной авторизации в Telegram
"""

import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

async def create_session():
    """Создание Telegram сессии"""
    print("="*60)
    print("🔐 Создание Telegram сессии")
    print("="*60)
    
    # Проверка наличия учетных данных
    if not API_ID or not API_HASH:
        print("❌ Ошибка: API_ID и API_HASH не найдены в .env файле")
        print("\n📝 Инструкция:")
        print("1. Перейдите на https://my.telegram.org/apps")
        print("2. Войдите под своим номером телефона")
        print("3. Создайте новое приложение")
        print("4. Скопируйте API ID и API Hash")
        print("5. Добавьте их в .env файл:")
        print("   API_ID=your_api_id")
        print("   API_HASH=your_api_hash")
        return
    
    if not PHONE_NUMBER:
        print("❌ Ошибка: PHONE_NUMBER не найден в .env файле")
        print("Добавьте номер телефона в формате: PHONE_NUMBER=+79001234567")
        return
    
    print(f"📱 Номер телефона: {PHONE_NUMBER}")
    print(f"🔑 API ID: {API_ID}")
    print(f"💾 Имя сессии: {SESSION_NAME}")
    print("="*60)
    
    try:
        # Создание клиента
        client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        # Подключение и авторизация
        await client.start(phone=PHONE_NUMBER)
        
        print("\n✅ Сессия успешно создана!")
        print(f"📁 Файл сессии: {SESSION_NAME}.session")
        
        # Получение информации о себе
        me = await client.get_me()
        print("\n👤 Информация об аккаунте:")
        print(f"   Имя: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username or 'не указан'}")
        print(f"   ID: {me.id}")
        
        print("\n✅ Теперь вы можете запустить bot_automation.py")
        print("="*60)
        
        # Отключение
        await client.disconnect()
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании сессии: {e}")
        print("\n💡 Возможные причины:")
        print("1. Неверный API_ID или API_HASH")
        print("2. Неверный номер телефона")
        print("3. Проблемы с подключением к Telegram")
        print("\n📝 Проверьте данные в .env файле и попробуйте снова")

if __name__ == "__main__":
    asyncio.run(create_session())






