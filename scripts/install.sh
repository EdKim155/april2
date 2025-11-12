#!/bin/bash

# Скрипт установки April Bot на сервер

set -e

echo "🚀 Установка April Bot..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Установка директории
INSTALL_DIR="/opt/april_bot"
USER="april_bot"

# Остановка старых процессов
echo -e "${YELLOW}Остановка существующих процессов бота...${NC}"
systemctl stop april_bot.service 2>/dev/null || true
pkill -f "python.*bot" || true
pkill -f "python.*main.py" || true
sleep 2

# Создание пользователя
if ! id -u $USER > /dev/null 2>&1; then
    echo -e "${YELLOW}Создание пользователя $USER...${NC}"
    useradd -r -s /bin/bash -d $INSTALL_DIR $USER
fi

# Установка зависимостей системы
echo -e "${YELLOW}Установка системных зависимостей...${NC}"
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql postgresql-contrib

# Создание директории
echo -e "${YELLOW}Создание директории $INSTALL_DIR...${NC}"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Копирование файлов (будет сделано через rsync)
echo -e "${GREEN}Файлы должны быть скопированы через rsync${NC}"

# Создание виртуального окружения
echo -e "${YELLOW}Создание виртуального окружения...${NC}"
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
echo -e "${YELLOW}Установка зависимостей Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Настройка базы данных PostgreSQL
echo -e "${YELLOW}Настройка базы данных...${NC}"
sudo -u postgres psql -c "CREATE DATABASE april_bot;" 2>/dev/null || echo "База данных уже существует"
sudo -u postgres psql -c "CREATE USER april_user WITH PASSWORD 'secure_password_here';" 2>/dev/null || echo "Пользователь уже существует"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE april_bot TO april_user;"

# Установка прав
echo -e "${YELLOW}Установка прав доступа...${NC}"
chown -R $USER:$USER $INSTALL_DIR
chmod 755 $INSTALL_DIR

# Создание systemd service
echo -e "${YELLOW}Создание systemd service...${NC}"
cat > /etc/systemd/system/april_bot.service << 'EOF'
[Unit]
Description=April Telegram Bot
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=april_bot
Group=april_bot
WorkingDirectory=/opt/april_bot
Environment="PATH=/opt/april_bot/venv/bin"
ExecStart=/opt/april_bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10
StandardOutput=append:/opt/april_bot/bot.log
StandardError=append:/opt/april_bot/bot.log

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
systemctl daemon-reload

echo -e "${GREEN}✅ Установка завершена!${NC}"
echo -e "${YELLOW}Не забудьте:${NC}"
echo "1. Настроить файл .env в $INSTALL_DIR"
echo "2. Добавить Google Sheets credentials в $INSTALL_DIR/credentials/"
echo "3. Запустить бота: systemctl start april_bot"
echo "4. Включить автозапуск: systemctl enable april_bot"






