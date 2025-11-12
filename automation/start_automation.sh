#\!/bin/bash

# Скрипт для запуска бота автоматизации

cd /root/automation
source venv/bin/activate

echo "🤖 Запуск бота автоматизации..."
echo "📝 Логи будут сохраняться в automation.log"
echo ""

# Запуск бота с перенаправлением вывода в лог
nohup python bot_automation.py >> automation.log 2>&1 &

PID=$\!
echo "✅ Бот запущен с PID: $PID"
echo ""
echo "📊 Команды для мониторинга:"
echo "  - Просмотр логов в реальном времени: tail -f /root/automation/automation.log"
echo "  - Последние 50 строк логов: tail -50 /root/automation/automation.log"
echo "  - Проверка процесса: ps aux | grep bot_automation"
echo "  - Остановка бота: kill $PID"
echo ""
