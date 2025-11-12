#!/bin/bash

# Скрипт деплоя April Bot на удаленный сервер

set -e

# Настройки
SERVER="root@72.56.76.248"
SSH_KEY="$HOME/.ssh/id_ed25519_aprel"
REMOTE_DIR="/opt/april_bot"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Деплой April Bot на сервер..."

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Проверка SSH ключа
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}❌ SSH ключ не найден: $SSH_KEY${NC}"
    exit 1
fi

# Остановка старого бота
echo -e "${YELLOW}Шаг 1: Остановка старого бота...${NC}"
ssh -i "$SSH_KEY" "$SERVER" "bash -s" < "$LOCAL_DIR/deploy/stop_old_bot.sh"

# Создание резервной копии (если есть)
echo -e "${YELLOW}Шаг 2: Создание резервной копии...${NC}"
ssh -i "$SSH_KEY" "$SERVER" << 'EOF'
if [ -d "/opt/april_bot" ]; then
    echo "Создание резервной копии..."
    tar -czf "/root/april_bot_backup_$(date +%Y%m%d_%H%M%S).tar.gz" -C /opt april_bot 2>/dev/null || true
    echo "✅ Резервная копия создана"
fi
EOF

# Создание директории
echo -e "${YELLOW}Шаг 3: Подготовка директории...${NC}"
ssh -i "$SSH_KEY" "$SERVER" "mkdir -p $REMOTE_DIR"

# Копирование файлов
echo -e "${YELLOW}Шаг 4: Копирование файлов...${NC}"
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude 'bot.log' \
    --exclude 'bot_automation.log' \
    --exclude '.env' \
    --exclude 'telegram_session.session' \
    -e "ssh -i $SSH_KEY" \
    "$LOCAL_DIR/" "$SERVER:$REMOTE_DIR/"

# Установка и настройка
echo -e "${YELLOW}Шаг 5: Установка на сервере...${NC}"
ssh -i "$SSH_KEY" "$SERVER" "cd $REMOTE_DIR && bash deploy/install.sh"

echo -e "${GREEN}✅ Деплой завершен!${NC}"
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "1. ssh -i $SSH_KEY $SERVER"
echo "2. cd $REMOTE_DIR"
echo "3. nano .env  # Настройте переменные окружения"
echo "4. systemctl start april_bot"
echo "5. systemctl status april_bot"
echo "6. systemctl enable april_bot  # Для автозапуска"





