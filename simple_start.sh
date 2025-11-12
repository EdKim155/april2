#!/bin/bash
# Скрипт запуска упрощенной автоматизации

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/simple_button_automation.py"
LOG_FILE="$SCRIPT_DIR/simple_automation.log"
PID_FILE="$SCRIPT_DIR/simple_automation.pid"

echo "🚀 Запуск упрощенной автоматизации..."

# Проверяем, не запущен ли уже бот
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Бот уже запущен (PID: $OLD_PID)"
        echo "Используйте ./simple_stop.sh для остановки"
        exit 1
    else
        echo "🧹 Удаляю старый PID файл"
        rm -f "$PID_FILE"
    fi
fi

# Проверяем наличие Python скрипта
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Ошибка: файл $PYTHON_SCRIPT не найден"
    exit 1
fi

# Активируем виртуальное окружение, если оно есть
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo "📦 Активация виртуального окружения..."
    source "$SCRIPT_DIR/venv/bin/activate"
    PYTHON_CMD="python"
else
    # Используем системный Python
    PYTHON_CMD="python3"
fi

# Запускаем бота в фоне
echo "▶️  Запуск бота..."
nohup $PYTHON_CMD "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
BOT_PID=$!

# Сохраняем PID
echo $BOT_PID > "$PID_FILE"

# Ждем немного и проверяем, что процесс запустился
sleep 1
if ps -p $BOT_PID > /dev/null 2>&1; then
    echo "✅ Бот успешно запущен (PID: $BOT_PID)"
    echo "📄 Логи: $LOG_FILE"
    echo ""
    echo "Команды:"
    echo "  • Остановить: ./simple_stop.sh"
    echo "  • Просмотр логов: tail -f simple_automation.log"
else
    echo "❌ Ошибка запуска. Проверьте логи: $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi
