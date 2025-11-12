#!/bin/bash
# Скрипт развертывания упрощенной автоматизации на сервере

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     РАЗВЕРТЫВАНИЕ УПРОЩЕННОЙ АВТОМАТИЗАЦИИ НА СЕРВЕРЕ           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Директория для установки
INSTALL_DIR="/root/simple_automation"

echo -e "${YELLOW}📁 Директория установки: ${INSTALL_DIR}${NC}"
echo ""

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

# Шаг 1: Установка Python и pip
echo -e "${BLUE}[1/7]${NC} Проверка Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}📦 Установка Python3...${NC}"
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv
else
    echo -e "${GREEN}✓ Python3 установлен: $(python3 --version)${NC}"
fi

# Шаг 2: Создание директории
echo -e "${BLUE}[2/7]${NC} Создание директории..."
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"
echo -e "${GREEN}✓ Директория создана: $INSTALL_DIR${NC}"

# Шаг 3: Создание виртуального окружения
echo -e "${BLUE}[3/7]${NC} Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Виртуальное окружение создано${NC}"
else
    echo -e "${YELLOW}⚠️  Виртуальное окружение уже существует${NC}"
fi

# Активация виртуального окружения
source venv/bin/activate

# Шаг 4: Установка зависимостей
echo -e "${BLUE}[4/7]${NC} Установка зависимостей..."
pip install --upgrade pip -q
pip install telethon -q
echo -e "${GREEN}✓ Зависимости установлены${NC}"

# Шаг 5: Копирование файлов
echo -e "${BLUE}[5/7]${NC} Копирование файлов..."

# Проверка, откуда запущен скрипт
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Список файлов для копирования
FILES=(
    "simple_button_automation.py"
    "simple_start.sh"
    "simple_stop.sh"
    "simple_automation_session.session"
)

for file in "${FILES[@]}"; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp "$SCRIPT_DIR/$file" "$INSTALL_DIR/"
        echo -e "${GREEN}  ✓ Скопирован: $file${NC}"
    else
        echo -e "${RED}  ❌ Не найден: $file${NC}"
        if [ "$file" == "simple_automation_session.session" ]; then
            echo -e "${YELLOW}     ⚠️  Файл сессии отсутствует! Запустите create_simple_session.py локально${NC}"
        fi
    fi
done

# Установка прав на выполнение
chmod +x "$INSTALL_DIR/simple_button_automation.py"
chmod +x "$INSTALL_DIR/simple_start.sh"
chmod +x "$INSTALL_DIR/simple_stop.sh"

# Установка прав безопасности
chmod 600 "$INSTALL_DIR/simple_automation_session.session" 2>/dev/null || true

echo -e "${GREEN}✓ Файлы скопированы${NC}"

# Шаг 6: Создание systemd сервиса
echo -e "${BLUE}[6/7]${NC} Создание systemd сервиса..."

cat > /etc/systemd/system/simple-automation.service << EOF
[Unit]
Description=Simple Telegram Button Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/simple_button_automation.py
Restart=always
RestartSec=10
StandardOutput=append:${INSTALL_DIR}/simple_automation.log
StandardError=append:${INSTALL_DIR}/simple_automation.log

# Безопасность
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Systemd сервис создан${NC}"

# Перезагрузка systemd
systemctl daemon-reload

# Шаг 7: Включение автозапуска
echo -e "${BLUE}[7/7]${NC} Настройка автозапуска..."
systemctl enable simple-automation.service
echo -e "${GREEN}✓ Автозапуск включен${NC}"

# Финал
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    ✅ УСТАНОВКА ЗАВЕРШЕНА!                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📁 Установлено в: ${INSTALL_DIR}${NC}"
echo ""
echo -e "${YELLOW}Команды управления:${NC}"
echo ""
echo -e "  ${GREEN}Запуск:${NC}"
echo -e "    systemctl start simple-automation"
echo ""
echo -e "  ${GREEN}Остановка:${NC}"
echo -e "    systemctl stop simple-automation"
echo ""
echo -e "  ${GREEN}Перезапуск:${NC}"
echo -e "    systemctl restart simple-automation"
echo ""
echo -e "  ${GREEN}Статус:${NC}"
echo -e "    systemctl status simple-automation"
echo ""
echo -e "  ${GREEN}Логи (реального времени):${NC}"
echo -e "    tail -f ${INSTALL_DIR}/simple_automation.log"
echo ""
echo -e "  ${GREEN}Логи (systemd):${NC}"
echo -e "    journalctl -u simple-automation -f"
echo ""
echo -e "${YELLOW}⚠️  ВАЖНО:${NC}"
echo -e "   1. Убедитесь, что файл simple_automation_session.session скопирован"
echo -e "   2. Запустите сервис: ${GREEN}systemctl start simple-automation${NC}"
echo -e "   3. Проверьте логи: ${GREEN}tail -f ${INSTALL_DIR}/simple_automation.log${NC}"
echo ""
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
