#!/bin/bash

# Скрипт для настройки .env и запуска бота

set -e

echo "⚙️ Настройка и запуск April Bot..."

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте файл .env со следующими переменными:"
    echo ""
    echo "BOT_TOKEN=ваш_токен_бота"
    echo "DB_HOST=localhost"
    echo "DB_PORT=5432"
    echo "DB_NAME=april_bot"
    echo "DB_USER=april_user"
    echo "DB_PASSWORD=secure_password_here"
    echo "GOOGLE_SHEET_ID=ваш_id_таблицы"
    echo ""
    echo "Введите BOT_TOKEN:"
    read -r BOT_TOKEN
    
    echo "Введите GOOGLE_SHEET_ID:"
    read -r GOOGLE_SHEET_ID
    
    # Создание .env файла
    cat > .env << EOF
# Telegram Bot
BOT_TOKEN=$BOT_TOKEN

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=april_bot
DB_USER=april_user
DB_PASSWORD=secure_password_here

# Google Sheets Configuration
GOOGLE_SHEET_ID=$GOOGLE_SHEET_ID
GOOGLE_CREDENTIALS_FILE=/opt/april_bot/credentials/perevoz-477307-34872f231d9b.json
GOOGLE_SHEET_NAME=Перевозки
SYNC_INTERVAL=10

# Timezone
TIMEZONE=Europe/Moscow

# Scheduler Configuration
PUBLISH_HOUR=11
PUBLISH_MINUTE=30

# Logging
LOG_LEVEL=INFO

# Rate Limiting
MAX_BOOKINGS_PER_MINUTE=10
EOF
    
    echo "✅ Файл .env создан"
fi

# Включение и запуск сервиса
echo "🚀 Запуск бота..."
systemctl enable april_bot
systemctl start april_bot

# Проверка статуса
sleep 2
systemctl status april_bot --no-pager

echo ""
echo "✅ Бот запущен!"
echo "Просмотр логов: journalctl -u april_bot -f"
echo "Остановка бота: systemctl stop april_bot"
echo "Перезапуск бота: systemctl restart april_bot"

