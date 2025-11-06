#!/bin/bash

# Быстрая настройка и запуск бота на сервере

SERVER="root@72.56.76.248"
SSH_KEY="$HOME/.ssh/id_ed25519_aprel"

echo "🔧 Быстрая настройка April Bot на сервере"
echo ""
echo "Введите BOT_TOKEN:"
read -r BOT_TOKEN

echo "Введите GOOGLE_SHEET_ID:"
read -r GOOGLE_SHEET_ID

echo "Введите пароль для БД (или Enter для генерации):"
read -r DB_PASSWORD

if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 32)
    echo "Сгенерирован пароль: $DB_PASSWORD"
fi

# Создание .env на сервере
ssh -i "$SSH_KEY" "$SERVER" "cd /opt/april_bot && cat > .env" << EOF
# Telegram Bot
BOT_TOKEN=$BOT_TOKEN

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=april_bot
DB_USER=april_user
DB_PASSWORD=$DB_PASSWORD

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

# Обновление пароля в БД
echo "🔐 Обновление пароля базы данных..."
ssh -i "$SSH_KEY" "$SERVER" << EOSSH
sudo -u postgres psql -c "ALTER USER april_user WITH PASSWORD '$DB_PASSWORD';"
EOSSH

# Запуск бота
echo "🚀 Запуск бота..."
ssh -i "$SSH_KEY" "$SERVER" << 'EOSSH'
systemctl enable april_bot
systemctl start april_bot
sleep 3
systemctl status april_bot --no-pager -l
EOSSH

echo ""
echo "✅ Готово!"
echo ""
echo "Команды для управления:"
echo "  Просмотр логов:  ssh -i $SSH_KEY $SERVER 'journalctl -u april_bot -f'"
echo "  Перезапуск:      ssh -i $SSH_KEY $SERVER 'systemctl restart april_bot'"
echo "  Остановка:       ssh -i $SSH_KEY $SERVER 'systemctl stop april_bot'"
echo "  Статус:          ssh -i $SSH_KEY $SERVER 'systemctl status april_bot'"

