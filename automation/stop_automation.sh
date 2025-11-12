#\!/bin/bash

# Скрипт для остановки бота автоматизации

echo "⏹️  Остановка бота автоматизации..."

pkill -f "python bot_automation.py"

sleep 2

if ps aux | grep -v grep | grep "bot_automation.py" > /dev/null; then
    echo "❌ Не удалось остановить бот"
    echo "Попытка принудительной остановки..."
    pkill -9 -f "python bot_automation.py"
    sleep 1
    if ps aux | grep -v grep | grep "bot_automation.py" > /dev/null; then
        echo "❌ Бот все еще работает, проверьте вручную"
    else
        echo "✅ Бот принудительно остановлен"
    fi
else
    echo "✅ Бот успешно остановлен"
fi
