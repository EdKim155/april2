#!/bin/bash
# Скрипт быстрого деплоя ULTRA-FAST версии v2.2

set -e  # Остановка при ошибке

echo "=========================================="
echo "🚀 ДЕПЛОЙ ULTRA-FAST v2.2"
echo "=========================================="
echo ""

# Конфигурация
SERVER_USER="root"
SERVER_IP="72.56.76.248"
SSH_KEY="~/.ssh/id_ed25519_aprel"
REMOTE_DIR="/root/automation"

# Проверка наличия файлов
echo "1️⃣ Проверка файлов..."
if [ ! -f "bot_automation.py" ]; then
    echo "❌ Файл bot_automation.py не найден!"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo "❌ Файл config.py не найден!"
    exit 1
fi

echo "✅ Все файлы на месте"
echo ""

# Создание бэкапа на сервере
echo "2️⃣ Создание бэкапа на сервере..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" "cd $REMOTE_DIR && cp bot_automation.py bot_automation.py.backup_$(date +%Y%m%d_%H%M%S) && cp config.py config.py.backup_$(date +%Y%m%d_%H%M%S)" || echo "⚠️ Бэкап не создан (возможно файлов еще нет)"
echo "✅ Бэкап создан"
echo ""

# Остановка старой версии
echo "3️⃣ Остановка старой версии..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" "cd $REMOTE_DIR && ./stop_automation.sh 2>/dev/null || pkill -f 'python.*bot_automation' || echo 'Бот уже остановлен'"
echo "✅ Остановлено"
echo ""

# Копирование файлов
echo "4️⃣ Копирование файлов на сервер..."
scp -i "$SSH_KEY" bot_automation.py "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"
scp -i "$SSH_KEY" config.py "$SERVER_USER@$SERVER_IP:$REMOTE_DIR/"
echo "✅ Файлы скопированы"
echo ""

# Запуск новой версии
echo "5️⃣ Запуск новой версии v2.2..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" "cd $REMOTE_DIR && ./start_automation.sh"
sleep 2
echo "✅ Запущено"
echo ""

# Проверка статуса
echo "6️⃣ Проверка статуса..."
ssh -i "$SSH_KEY" "$SERVER_USER@$SERVER_IP" "ps aux | grep 'bot_automation' | grep -v grep" || echo "⚠️ Процесс не найден, проверьте логи"
echo ""

echo "=========================================="
echo "✅ ДЕПЛОЙ ЗАВЕРШЕН!"
echo "=========================================="
echo ""
echo "📊 Для просмотра логов:"
echo "ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'tail -f $REMOTE_DIR/automation.log | grep -E \"(🚨|✅|⚠️|❌)\"'"
echo ""
echo "⏹️ Для остановки:"
echo "ssh -i $SSH_KEY $SERVER_USER@$SERVER_IP 'cd $REMOTE_DIR && ./stop_automation.sh'"
echo ""
