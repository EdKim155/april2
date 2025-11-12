#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных и добавления первых пользователей и сессий
"""

import os
import sys
from database import get_database
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

def main():
    """Главная функция инициализации"""
    print("="*60)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("="*60)

    # Создаем экземпляр БД (автоматически создаст таблицы)
    db = get_database()

    print("✓ База данных инициализирована")
    print("✓ Таблицы созданы: users, sessions, access_logs")
    print()

    # Добавление первого пользователя
    print("-"*60)
    print("ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ")
    print("-"*60)
    print()
    print("Чтобы получить ваш Telegram User ID:")
    print("1. Напишите боту @userinfobot в Telegram")
    print("2. Он покажет ваш User ID")
    print()

    try:
        user_id = input("Введите Telegram User ID: ").strip()
        user_id = int(user_id)

        username = input("Введите Telegram username (необязательно): ").strip() or None
        first_name = input("Введите имя (необязательно): ").strip() or None

        if db.add_user(user_id, username, first_name):
            print(f"\n✓ Пользователь {user_id} добавлен успешно!")
        else:
            print(f"\n❌ Ошибка при добавлении пользователя")
    except ValueError:
        print("\n❌ Неверный формат User ID")
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
        return

    # Добавление сессии
    print()
    print("-"*60)
    print("ДОБАВЛЕНИЕ СЕССИИ АВТОМАТИЗАЦИИ")
    print("-"*60)
    print()

    add_session = input("Хотите добавить сессию автоматизации? (y/n): ").strip().lower()

    if add_session == 'y':
        try:
            session_name = input("Название сессии (например, 'Аккаунт 1'): ").strip()
            phone_number = input("Номер телефона (например, +79512586335): ").strip()

            # Пытаемся получить из .env
            api_id = os.getenv('API_ID')
            api_hash = os.getenv('API_HASH')

            if not api_id or not api_hash:
                print("\nПеременные API_ID и API_HASH не найдены в .env")
                api_id = input("Введите API_ID: ").strip()
                api_hash = input("Введите API_HASH: ").strip()
            else:
                print(f"\n✓ Используем API_ID и API_HASH из .env")

            api_id = int(api_id)

            session_file = input("Путь к файлу сессии (например, sessions/session1.session): ").strip()

            session_id = db.add_session(
                session_name=session_name,
                phone_number=phone_number,
                api_id=api_id,
                api_hash=api_hash,
                session_file=session_file
            )

            if session_id:
                print(f"\n✓ Сессия '{session_name}' добавлена с ID {session_id}")
                print(f"\nТеперь вы можете:")
                print(f"1. Создать файл сессии Telegram:")
                print(f"   python simple_button_automation.py {api_id} {api_hash} {phone_number} {session_file} @ACarriers_bot {session_id}")
                print(f"2. Запустить Control Bot и управлять сессией через Telegram")
            else:
                print("\n❌ Ошибка при добавлении сессии")

        except ValueError as e:
            print(f"\n❌ Ошибка: {e}")
        except KeyboardInterrupt:
            print("\n\nОтменено пользователем")

    print()
    print("="*60)
    print("ИНИЦИАЛИЗАЦИЯ ЗАВЕРШЕНА")
    print("="*60)
    print()
    print("Следующие шаги:")
    print("1. Создайте .env файл на основе .env.example")
    print("2. Установите зависимости: pip install -r requirements.txt")
    print("3. Запустите Control Bot: python control_bot.py")
    print()
    print("Документация:")
    print("- README.md - полная инструкция по установке и использованию")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
