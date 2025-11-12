# 🚀 Развертывание на сервере - Пошаговая инструкция

## Метод 1: Автоматическое развертывание (Рекомендуется)

### Подготовка локально

```bash
# 1. Создайте архив с необходимыми файлами
cd /Users/edgark/Desktop/april2
tar -czf simple_automation_deploy.tar.gz \
    simple_button_automation.py \
    simple_start.sh \
    simple_stop.sh \
    simple_automation_session.session \
    deploy_simple_automation.sh
```

### Развертывание на сервере

```bash
# 2. Скопируйте архив на сервер (замените SERVER_IP)
scp simple_automation_deploy.tar.gz root@SERVER_IP:/tmp/

# 3. Подключитесь к серверу
ssh root@SERVER_IP

# 4. Распакуйте архив
cd /tmp
tar -xzf simple_automation_deploy.tar.gz

# 5. Запустите скрипт развертывания
chmod +x deploy_simple_automation.sh
./deploy_simple_automation.sh

# 6. Запустите сервис
systemctl start simple-automation

# 7. Проверьте статус
systemctl status simple-automation
```

---

## Метод 2: Ручное развертывание

### Шаг 1: Подключение к серверу

```bash
ssh root@YOUR_SERVER_IP
```

### Шаг 2: Установка зависимостей

```bash
# Обновление системы
apt-get update

# Установка Python и pip
apt-get install -y python3 python3-pip python3-venv

# Проверка установки
python3 --version
```

### Шаг 3: Создание директории

```bash
mkdir -p /root/simple_automation
cd /root/simple_automation
```

### Шаг 4: Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install telethon
```

### Шаг 5: Копирование файлов

**С локальной машины** откройте новый терминал:

```bash
# Перейдите в директорию проекта
cd /Users/edgark/Desktop/april2

# Скопируйте файлы на сервер (замените SERVER_IP)
scp simple_button_automation.py root@SERVER_IP:/root/simple_automation/
scp simple_start.sh root@SERVER_IP:/root/simple_automation/
scp simple_stop.sh root@SERVER_IP:/root/simple_automation/
scp simple_automation_session.session root@SERVER_IP:/root/simple_automation/
```

### Шаг 6: Настройка прав (на сервере)

```bash
cd /root/simple_automation

# Права на выполнение
chmod +x simple_button_automation.py
chmod +x simple_start.sh
chmod +x simple_stop.sh

# Безопасность сессии
chmod 600 simple_automation_session.session
```

### Шаг 7: Создание systemd сервиса

```bash
cat > /etc/systemd/system/simple-automation.service << 'EOF'
[Unit]
Description=Simple Telegram Button Automation
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/simple_automation
ExecStart=/root/simple_automation/venv/bin/python /root/simple_automation/simple_button_automation.py
Restart=always
RestartSec=10
StandardOutput=append:/root/simple_automation/simple_automation.log
StandardError=append:/root/simple_automation/simple_automation.log

# Безопасность
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
```

### Шаг 8: Активация сервиса

```bash
# Перезагрузка конфигурации systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable simple-automation

# Запуск сервиса
systemctl start simple-automation

# Проверка статуса
systemctl status simple-automation
```

---

## Команды управления на сервере

### Основные команды

```bash
# Запуск
systemctl start simple-automation

# Остановка
systemctl stop simple-automation

# Перезапуск
systemctl restart simple-automation

# Статус
systemctl status simple-automation

# Включить автозапуск
systemctl enable simple-automation

# Отключить автозапуск
systemctl disable simple-automation
```

### Просмотр логов

```bash
# Логи в реальном времени (файл)
tail -f /root/simple_automation/simple_automation.log

# Логи в реальном времени (systemd)
journalctl -u simple-automation -f

# Последние 100 строк логов
tail -100 /root/simple_automation/simple_automation.log

# Поиск ошибок
grep -i "error\|ошибка" /root/simple_automation/simple_automation.log

# Статистика
grep "СТАТИСТИКА" /root/simple_automation/simple_automation.log
```

---

## Проверка работы

### 1. Проверка статуса сервиса

```bash
systemctl status simple-automation
```

**Ожидаемый вывод:**
```
● simple-automation.service - Simple Telegram Button Automation
     Loaded: loaded (/etc/systemd/system/simple-automation.service; enabled)
     Active: active (running) since ...
```

### 2. Проверка процесса

```bash
ps aux | grep simple_button_automation
```

### 3. Проверка логов

```bash
tail -50 /root/simple_automation/simple_automation.log
```

**Должно быть:**
```
🤖 УПРОЩЕННЫЙ БОТ ЗАПУЩЕН
🎯 Триггер: "Появились новые перевозки"
🔘 Целевая кнопка: "🔔Список прямых перевозок"
```

### 4. Проверка сети

```bash
# Проверка подключения к Telegram
netstat -tulpn | grep python

# Или
ss -tulpn | grep python
```

---

## Мониторинг

### Создание скрипта мониторинга

```bash
cat > /root/simple_automation/monitor.sh << 'EOF'
#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           МОНИТОРИНГ АВТОМАТИЗАЦИИ                             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Статус сервиса
echo "📊 Статус сервиса:"
systemctl is-active simple-automation && echo "  ✅ Запущен" || echo "  ❌ Остановлен"
echo ""

# Процесс
echo "🔍 Процесс:"
ps aux | grep simple_button_automation | grep -v grep || echo "  ❌ Процесс не найден"
echo ""

# Последние логи
echo "📝 Последние логи (10 строк):"
tail -10 /root/simple_automation/simple_automation.log
echo ""

# Статистика
echo "📈 Статистика:"
grep "СТАТИСТИКА" /root/simple_automation/simple_automation.log | tail -1
echo ""

# Ошибки
echo "⚠️  Последние ошибки:"
grep -i "error\|ошибка" /root/simple_automation/simple_automation.log | tail -5 || echo "  ✅ Ошибок нет"

echo ""
echo "╚════════════════════════════════════════════════════════════════╝"
EOF

chmod +x /root/simple_automation/monitor.sh
```

**Использование:**
```bash
/root/simple_automation/monitor.sh
```

---

## Обновление

### Обновление файлов

```bash
# 1. Остановите сервис
systemctl stop simple-automation

# 2. Скопируйте новые файлы с локальной машины
scp simple_button_automation.py root@SERVER_IP:/root/simple_automation/

# 3. Запустите сервис
systemctl start simple-automation

# 4. Проверьте логи
tail -f /root/simple_automation/simple_automation.log
```

---

## Устранение неполадок

### Проблема: Сервис не запускается

```bash
# Проверьте логи systemd
journalctl -u simple-automation -n 50

# Проверьте файл сессии
ls -la /root/simple_automation/simple_automation_session.session

# Попробуйте запустить вручную
cd /root/simple_automation
source venv/bin/activate
python simple_button_automation.py
```

### Проблема: Нет файла сессии

```bash
# Скопируйте сессию с локальной машины
scp simple_automation_session.session root@SERVER_IP:/root/simple_automation/

# Установите права
chmod 600 /root/simple_automation/simple_automation_session.session
```

### Проблема: Бот не нажимает кнопку

```bash
# Проверьте логи на наличие триггера
grep "ТРИГГЕР" /root/simple_automation/simple_automation.log

# Проверьте подключение к боту
grep "Подключен к боту" /root/simple_automation/simple_automation.log

# Проверьте сохранение клавиатуры
grep "Сохранена клавиатура" /root/simple_automation/simple_automation.log
```

---

## Автоматическая очистка логов

### Настройка ротации логов

```bash
cat > /etc/logrotate.d/simple-automation << 'EOF'
/root/simple_automation/simple_automation.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        systemctl reload simple-automation > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

## Безопасность

### Файрвол (опционально)

```bash
# Если используется UFW
ufw allow 22/tcp
ufw enable
```

### Права доступа

```bash
# Проверка прав
ls -la /root/simple_automation/

# Должно быть:
# -rwx------ simple_automation_session.session
# -rwxr-xr-x simple_button_automation.py
# -rwxr-xr-x simple_start.sh
# -rwxr-xr-x simple_stop.sh
```

---

## Быстрая команда для развертывания

Одной командой (с локальной машины):

```bash
cd /Users/edgark/Desktop/april2 && \
tar -czf simple_automation_deploy.tar.gz \
    simple_button_automation.py \
    simple_start.sh \
    simple_stop.sh \
    simple_automation_session.session \
    deploy_simple_automation.sh && \
scp simple_automation_deploy.tar.gz root@YOUR_SERVER_IP:/tmp/ && \
ssh root@YOUR_SERVER_IP "cd /tmp && tar -xzf simple_automation_deploy.tar.gz && chmod +x deploy_simple_automation.sh && ./deploy_simple_automation.sh && systemctl start simple-automation && systemctl status simple-automation"
```

**Замените YOUR_SERVER_IP на IP вашего сервера!**

---

## Резюме команд

```bash
# РАЗВЕРТЫВАНИЕ (одной командой)
tar -czf simple_automation_deploy.tar.gz simple_button_automation.py simple_start.sh simple_stop.sh simple_automation_session.session deploy_simple_automation.sh && scp simple_automation_deploy.tar.gz root@SERVER_IP:/tmp/ && ssh root@SERVER_IP "cd /tmp && tar -xzf simple_automation_deploy.tar.gz && chmod +x deploy_simple_automation.sh && ./deploy_simple_automation.sh && systemctl start simple-automation"

# ЗАПУСК НА СЕРВЕРЕ
systemctl start simple-automation

# ПРОВЕРКА
systemctl status simple-automation
tail -f /root/simple_automation/simple_automation.log

# МОНИТОРИНГ
/root/simple_automation/monitor.sh
```

Готово! 🚀
