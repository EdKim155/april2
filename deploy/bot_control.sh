#!/bin/bash

# Утилита управления April Bot

SERVER="root@72.56.76.248"
SSH_KEY="$HOME/.ssh/id_ed25519_aprel"

case "$1" in
    status)
        echo "📊 Статус бота:"
        ssh -i "$SSH_KEY" "$SERVER" 'systemctl status april_bot --no-pager'
        ;;
    start)
        echo "▶️ Запуск бота..."
        ssh -i "$SSH_KEY" "$SERVER" 'systemctl start april_bot && systemctl status april_bot --no-pager'
        ;;
    stop)
        echo "⏸️ Остановка бота..."
        ssh -i "$SSH_KEY" "$SERVER" 'systemctl stop april_bot && systemctl status april_bot --no-pager'
        ;;
    restart)
        echo "🔄 Перезапуск бота..."
        ssh -i "$SSH_KEY" "$SERVER" 'systemctl restart april_bot && systemctl status april_bot --no-pager'
        ;;
    logs)
        echo "📋 Логи бота (Ctrl+C для выхода):"
        ssh -i "$SSH_KEY" "$SERVER" 'journalctl -u april_bot -f'
        ;;
    logs-last)
        echo "📋 Последние 50 строк логов:"
        ssh -i "$SSH_KEY" "$SERVER" 'journalctl -u april_bot -n 50 --no-pager'
        ;;
    shell)
        echo "🔗 Подключение к серверу..."
        ssh -i "$SSH_KEY" "$SERVER"
        ;;
    update)
        echo "🔄 Обновление бота на сервере..."
        cd "$(dirname "$0")/.."
        bash deploy/deploy.sh
        echo ""
        echo "Перезапустить бота? (y/n)"
        read -r answer
        if [ "$answer" = "y" ]; then
            ssh -i "$SSH_KEY" "$SERVER" 'systemctl restart april_bot'
            echo "✅ Бот перезапущен"
        fi
        ;;
    backup)
        echo "💾 Создание резервной копии..."
        ssh -i "$SSH_KEY" "$SERVER" "tar -czf /root/april_bot_manual_$(date +%Y%m%d_%H%M%S).tar.gz -C /opt april_bot"
        echo "✅ Резервная копия создана"
        ;;
    *)
        echo "🤖 April Bot - Утилита управления"
        echo ""
        echo "Использование: $0 {команда}"
        echo ""
        echo "Команды:"
        echo "  status      - Показать статус бота"
        echo "  start       - Запустить бота"
        echo "  stop        - Остановить бота"
        echo "  restart     - Перезапустить бота"
        echo "  logs        - Показать логи в реальном времени"
        echo "  logs-last   - Показать последние 50 строк логов"
        echo "  shell       - Подключиться к серверу по SSH"
        echo "  update      - Обновить код на сервере"
        echo "  backup      - Создать резервную копию"
        echo ""
        echo "Примеры:"
        echo "  $0 status"
        echo "  $0 logs"
        echo "  $0 restart"
        exit 1
        ;;
esac





