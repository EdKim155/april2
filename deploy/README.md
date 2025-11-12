# Инструкции по деплою April Bot

## Быстрый запуск

Для автоматической настройки и запуска бота выполните:

```bash
cd /Users/edgark/Desktop/april2
bash deploy/setup_env.sh
```

Скрипт запросит:
- `BOT_TOKEN` - токен Telegram бота
- `GOOGLE_SHEET_ID` - ID Google таблицы
- `DB_PASSWORD` - пароль для БД (можно пропустить для автогенерации)

После ввода данных бот будет автоматически настроен и запущен.

## Ручная настройка

### 1. Деплой файлов на сервер

```bash
bash deploy/deploy.sh
```

### 2. Настройка переменных окружения

Подключитесь к серверу:

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248
cd /opt/april_bot
nano .env
```

Заполните обязательные переменные:
- `BOT_TOKEN`
- `GOOGLE_SHEET_ID`
- `DB_PASSWORD`

### 3. Запуск бота

```bash
systemctl enable april_bot
systemctl start april_bot
systemctl status april_bot
```

## Управление ботом

### Просмотр логов в реальном времени

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'journalctl -u april_bot -f'
```

### Просмотр последних 100 строк логов

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'journalctl -u april_bot -n 100'
```

### Перезапуск бота

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'systemctl restart april_bot'
```

### Остановка бота

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'systemctl stop april_bot'
```

### Проверка статуса

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'systemctl status april_bot'
```

## Структура на сервере

- Директория бота: `/opt/april_bot`
- Systemd service: `/etc/systemd/system/april_bot.service`
- Логи: `journalctl -u april_bot` или `/opt/april_bot/bot.log`
- База данных: PostgreSQL, БД `april_bot`, пользователь `april_user`

## Обновление бота

Для обновления кода на сервере просто запустите деплой снова:

```bash
bash deploy/deploy.sh
```

После деплоя перезапустите бота:

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'systemctl restart april_bot'
```

## Резервное копирование

Автоматически создается резервная копия при каждом деплое в `/root/april_bot_backup_YYYYMMDD_HHMMSS.tar.gz`

Для ручного создания резервной копии:

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'tar -czf /root/april_bot_manual_backup.tar.gz -C /opt april_bot'
```

## Восстановление из резервной копии

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248
systemctl stop april_bot
rm -rf /opt/april_bot
tar -xzf /root/april_bot_backup_YYYYMMDD_HHMMSS.tar.gz -C /opt
systemctl start april_bot
```

## Автозапуск

Бот настроен на автоматический запуск при перезагрузке сервера через systemd.

Проверить статус автозапуска:

```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'systemctl is-enabled april_bot'
```

## Troubleshooting

### Бот не запускается

1. Проверьте логи:
```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'journalctl -u april_bot -n 100'
```

2. Проверьте .env файл:
```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'cat /opt/april_bot/.env'
```

3. Проверьте базу данных:
```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '\''april_bot'\'';"'
```

### База данных не подключается

Проверьте учетные данные:
```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'sudo -u postgres psql -d april_bot -c "SELECT current_user;"'
```

### Google Sheets не работает

Проверьте наличие credentials файла:
```bash
ssh -i ~/.ssh/id_ed25519_aprel root@72.56.76.248 'ls -la /opt/april_bot/credentials/'
```






