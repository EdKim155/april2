#!/usr/bin/env python3
"""
Telegram бот для управления автоматизацией April Shipments
Управление сессиями, режимами работы и мониторинг в реальном времени
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

from database import get_database
from session_manager import get_session_manager

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/control_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Конфигурация
CONTROL_BOT_TOKEN = os.getenv('CONTROL_BOT_TOKEN')
if not CONTROL_BOT_TOKEN:
    logger.error("CONTROL_BOT_TOKEN не найден в .env файле!")
    sys.exit(1)

# Глобальные экземпляры
db = get_database()
manager = get_session_manager()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def mask_phone_number(phone: str) -> str:
    """Маскировать номер телефона (скрыть средние цифры)"""
    if len(phone) < 8:
        return phone
    return f"{phone[:4]}***{phone[-4:]}"


def format_uptime(uptime_str: Optional[str]) -> str:
    """Форматировать время работы"""
    return uptime_str if uptime_str else "--:--:--"


def get_status_emoji(status: str) -> str:
    """Получить эмодзи для статуса"""
    return {
        'running': '🟢',
        'stopped': '⚫',
        'error': '🔴'
    }.get(status, '❓')


def get_mode_name(mode: int) -> str:
    """Получить название режима"""
    return {
        1: 'Режим 1 (1 кнопка)',
        2: 'Режим 2 (3 кнопки)'
    }.get(mode, 'Неизвестный режим')


# ==================== ПРОВЕРКА АВТОРИЗАЦИИ ====================

async def check_authorization(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Проверка авторизации пользователя

    Args:
        update: Update объект
        context: Context объект

    Returns:
        True если пользователь авторизован
    """
    user = update.effective_user
    user_id = user.id

    # Проверяем авторизацию
    if not db.is_user_authorized(user_id):
        # Логируем попытку доступа
        db.log_access(
            user_id=user_id,
            username=user.username or "Unknown",
            action="UNAUTHORIZED_ACCESS_ATTEMPT"
        )

        logger.warning(f"Неавторизованная попытка доступа: User ID {user_id}, Username: {user.username}")

        await update.message.reply_text(
            f"❌ Доступ запрещен.\n\n"
            f"Ваш Telegram User ID: `{user_id}`\n"
            f"Username: @{user.username or 'не указан'}\n\n"
            f"Обратитесь к администратору для получения доступа.",
            parse_mode='Markdown'
        )
        return False

    # Обновляем время последнего доступа
    db.update_last_access(user_id)

    return True


# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Управление сессиями", callback_data="menu_sessions")],
        [InlineKeyboardButton("📊 Мониторинг и логи", callback_data="menu_monitoring")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu_settings")],
        [InlineKeyboardButton("❓ Помощь", callback_data="menu_help")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    """Показать главное меню"""
    # Получаем статусы всех сессий
    sessions = db.get_all_sessions()

    if not sessions:
        status_text = "Нет активных сессий"
    else:
        status_lines = []
        for session in sessions:
            status = manager.check_session_status(session['id'])
            emoji = get_status_emoji(status['status'])
            mode_name = get_mode_name(status['mode'])
            status_lines.append(
                f"Сессия {session['id']}: {emoji} [{status['status'].upper()}] - {mode_name}"
            )
        status_text = "\n".join(status_lines)

    text = (
        "╔════════════════════════════════════════════╗\n"
        "║  УПРАВЛЕНИЕ АВТОМАТИЗАЦИЕЙ APRIL SHIPMENTS  ║\n"
        "╚════════════════════════════════════════════╝\n\n"
        f"Состояние системы:\n{status_text}\n"
    )

    keyboard = get_main_menu_keyboard()

    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text(text, reply_markup=keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    if not await check_authorization(update, context):
        return

    user = update.effective_user
    db.log_access(user.id, user.username or "Unknown", "START_COMMAND")

    await show_main_menu(update, context)


# ==================== УПРАВЛЕНИЕ СЕССИЯМИ ====================

async def menu_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню управления сессиями"""
    query = update.callback_query
    await query.answer()

    sessions = db.get_all_sessions()

    keyboard = []

    for session in sessions:
        status = manager.check_session_status(session['id'])
        emoji = get_status_emoji(status['status'])
        masked_phone = mask_phone_number(session['phone_number'])

        keyboard.append([
            InlineKeyboardButton(
                f"{emoji} {session['session_name']} ({masked_phone})",
                callback_data=f"session_{session['id']}"
            )
        ])

    keyboard.append([InlineKeyboardButton("➕ Добавить новую сессию", callback_data="session_add")])
    keyboard.append([InlineKeyboardButton("« Назад в меню", callback_data="menu_main")])

    text = (
        "╔════════════════════════════════════════════╗\n"
        "║         ВЫБЕРИТЕ СЕССИЮ                    ║\n"
        "╚════════════════════════════════════════════╝\n"
    )

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_session_control(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int):
    """Показать управление конкретной сессией"""
    query = update.callback_query
    if query:
        await query.answer()

    session = db.get_session(session_id)
    if not session:
        await query.edit_message_text("❌ Сессия не найдена")
        return

    status = manager.check_session_status(session_id)

    masked_phone = mask_phone_number(session['phone_number'])
    status_emoji = get_status_emoji(status['status'])
    mode_name = get_mode_name(status['mode'])
    uptime = format_uptime(status.get('uptime'))

    text = (
        f"╔════════════════════════════════════════════╗\n"
        f"║  СЕССИЯ {session_id}: {masked_phone}                    ║\n"
        f"║  Статус: {status_emoji} {status['status'].upper()}                          ║\n"
        f"║  Режим: {mode_name}              ║\n"
        f"║  Время работы: {uptime}                    ║\n"
        f"╚════════════════════════════════════════════╝\n"
    )

    keyboard = []

    # Основное управление
    if status['status'] == 'running':
        keyboard.append([InlineKeyboardButton("⏸ Остановить", callback_data=f"session_stop_{session_id}")])
    else:
        keyboard.append([InlineKeyboardButton("▶️ Запустить", callback_data=f"session_start_{session_id}")])

    keyboard.append([InlineKeyboardButton("🔄 Перезагрузить", callback_data=f"session_restart_{session_id}")])

    # Выбор режима
    mode1_mark = "✓" if status['mode'] == 1 else " "
    mode2_mark = "✓" if status['mode'] == 2 else " "

    keyboard.append([
        InlineKeyboardButton(f"[{mode1_mark}] Режим 1: 1 кнопка", callback_data=f"session_mode_1_{session_id}")
    ])
    keyboard.append([
        InlineKeyboardButton(f"[{mode2_mark}] Режим 2: 3 кнопки", callback_data=f"session_mode_2_{session_id}")
    ])

    # Информация
    keyboard.append([
        InlineKeyboardButton("📊 Статистика", callback_data=f"session_stats_{session_id}"),
        InlineKeyboardButton("📄 Логи", callback_data=f"session_logs_{session_id}")
    ])

    # Настройки
    keyboard.append([
        InlineKeyboardButton("⚙️ Параметры режима", callback_data=f"session_params_{session_id}"),
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"session_edit_{session_id}")
    ])

    keyboard.append([InlineKeyboardButton("« Назад к списку", callback_data="menu_sessions")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def session_start(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int):
    """Запустить сессию"""
    query = update.callback_query
    await query.answer("Запуск сессии...")

    user = update.effective_user
    db.log_access(user.id, user.username or "Unknown", "START_SESSION", session_id)

    success = manager.start_session(session_id)

    if success:
        await query.answer("✓ Сессия запущена успешно!", show_alert=True)
    else:
        await query.answer("❌ Не удалось запустить сессию", show_alert=True)

    # Обновляем экран
    await show_session_control(update, context, session_id)


async def session_stop(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int):
    """Остановить сессию"""
    query = update.callback_query
    await query.answer("Остановка сессии...")

    user = update.effective_user
    db.log_access(user.id, user.username or "Unknown", "STOP_SESSION", session_id)

    success = manager.stop_session(session_id)

    if success:
        await query.answer("✓ Сессия остановлена успешно!", show_alert=True)
    else:
        await query.answer("❌ Не удалось остановить сессию", show_alert=True)

    # Обновляем экран
    await show_session_control(update, context, session_id)


async def session_restart(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int):
    """Перезапустить сессию"""
    query = update.callback_query
    await query.answer("Перезапуск сессии...")

    user = update.effective_user
    db.log_access(user.id, user.username or "Unknown", "RESTART_SESSION", session_id)

    success = manager.restart_session(session_id)

    if success:
        await query.answer("✓ Сессия перезапущена успешно!", show_alert=True)
    else:
        await query.answer("❌ Не удалось перезапустить сессию", show_alert=True)

    # Обновляем экран
    await show_session_control(update, context, session_id)


async def session_switch_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int, new_mode: int):
    """Переключить режим сессии"""
    query = update.callback_query

    session = db.get_session(session_id)
    if session['current_mode'] == new_mode:
        await query.answer(f"Сессия уже в режиме {new_mode}", show_alert=True)
        return

    # Сохраняем в контекст для подтверждения
    context.user_data['pending_mode_switch'] = {
        'session_id': session_id,
        'new_mode': new_mode
    }

    keyboard = [
        [
            InlineKeyboardButton("✓ Да", callback_data=f"session_mode_confirm_{session_id}_{new_mode}"),
            InlineKeyboardButton("✗ Нет", callback_data=f"session_{session_id}")
        ]
    ]

    text = (
        f"⚠️ ВНИМАНИЕ!\n\n"
        f"Вы хотите переключить режим на {get_mode_name(new_mode)}?\n\n"
        f"Сессия будет перезапущена.\n\n"
        f"Продолжить?"
    )

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def session_mode_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int, new_mode: int):
    """Подтвердить переключение режима"""
    query = update.callback_query
    await query.answer("Переключение режима...")

    user = update.effective_user
    db.log_access(user.id, user.username or "Unknown", f"SWITCH_MODE_TO_{new_mode}", session_id)

    success = manager.switch_mode(session_id, new_mode)

    if success:
        await query.answer(f"✓ Режим изменен на {get_mode_name(new_mode)}", show_alert=True)
    else:
        await query.answer("❌ Не удалось изменить режим", show_alert=True)

    # Очищаем контекст
    if 'pending_mode_switch' in context.user_data:
        del context.user_data['pending_mode_switch']

    # Обновляем экран
    await show_session_control(update, context, session_id)


# ==================== СТАТИСТИКА И ЛОГИ ====================

async def show_session_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int):
    """Показать статистику сессии"""
    query = update.callback_query
    await query.answer("Загрузка статистики...")

    status = manager.check_session_status(session_id)
    stats = manager.parse_log_stats(session_id)

    uptime = format_uptime(status.get('uptime'))
    mode_name = get_mode_name(status['mode'])

    text = (
        f"╔════════════════════════════════════════════╗\n"
        f"║  СТАТИСТИКА: СЕССИЯ {session_id}                      ║\n"
        f"╚════════════════════════════════════════════╝\n\n"
        f"Время работы: {uptime}\n"
        f"Режим: {mode_name}\n\n"
        f"Триггеров обнаружено: {stats['triggers']}\n"
        f"Кнопок нажато: {stats['buttons']}\n"
        f"Ошибок: {stats['errors']}\n\n"
        f"Последний триггер: {stats['last_trigger'] or 'Нет данных'}\n"
        f"Последнее действие: {stats['last_action'] or 'Нет данных'}\n"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data=f"session_stats_{session_id}")],
        [InlineKeyboardButton("« Назад", callback_data=f"session_{session_id}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_session_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, session_id: int, lines: int = 20):
    """Показать логи сессии"""
    query = update.callback_query
    await query.answer("Загрузка логов...")

    logs = manager.get_session_logs(session_id, lines=lines)

    # Форматируем логи
    log_text = ''.join(logs[-lines:])
    if len(log_text) > 3000:
        log_text = log_text[-3000:]

    text = (
        f"╔════════════════════════════════════════════╗\n"
        f"║  ЛОГИ: СЕССИЯ {session_id} (последние {lines} строк)       ║\n"
        f"╚════════════════════════════════════════════╝\n\n"
        f"```\n{log_text}\n```"
    )

    keyboard = [
        [
            InlineKeyboardButton("20 строк", callback_data=f"session_logs_{session_id}_20"),
            InlineKeyboardButton("50 строк", callback_data=f"session_logs_{session_id}_50")
        ],
        [
            InlineKeyboardButton("100 строк", callback_data=f"session_logs_{session_id}_100"),
            InlineKeyboardButton("200 строк", callback_data=f"session_logs_{session_id}_200")
        ],
        [InlineKeyboardButton("« Назад", callback_data=f"session_{session_id}")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


# ==================== МОНИТОРИНГ ====================

async def menu_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню мониторинга всех сессий"""
    query = update.callback_query
    await query.answer("Загрузка мониторинга...")

    statuses = manager.monitor_all_sessions()

    if not statuses:
        text = "Нет активных сессий для мониторинга"
    else:
        text = (
            "╔════════════════════════════════════════════╗\n"
            "║  МОНИТОРИНГ ВСЕХ СЕССИЙ                    ║\n"
            "╚════════════════════════════════════════════╝\n\n"
        )

        for status in statuses:
            emoji = get_status_emoji(status['status'])
            mode_name = get_mode_name(status['mode'])
            uptime = format_uptime(status.get('uptime'))

            text += (
                f"{emoji} Сессия {status['session_id']}: {status['status'].upper()}\n"
                f"   {mode_name} | Время: {uptime}\n"
                f"   Триггеры: {status['stats']['triggers']} | "
                f"Ошибки: {status['stats']['errors']}\n\n"
            )

    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="menu_monitoring")],
        [InlineKeyboardButton("« Назад в меню", callback_data="menu_main")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== НАСТРОЙКИ ====================

async def menu_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню настроек"""
    query = update.callback_query
    await query.answer()

    text = (
        "╔════════════════════════════════════════════╗\n"
        "║  НАСТРОЙКИ                                 ║\n"
        "╚════════════════════════════════════════════╝\n\n"
        "Раздел в разработке...\n"
    )

    keyboard = [
        [InlineKeyboardButton("« Назад в меню", callback_data="menu_main")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== ПОМОЩЬ ====================

async def menu_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню помощи"""
    query = update.callback_query
    await query.answer()

    text = (
        "╔════════════════════════════════════════════╗\n"
        "║  ПОМОЩЬ                                    ║\n"
        "╚════════════════════════════════════════════╝\n\n"
        "📋 Основные команды:\n"
        "/start - Главное меню\n"
        "/status - Быстрый статус всех сессий\n"
        "/sessions - Список сессий\n"
        "/help - Эта справка\n\n"
        "🤖 Режимы работы:\n\n"
        "Режим 1 (1 кнопка):\n"
        "  - Быстрое нажатие кнопки 'Список прямых перевозок'\n"
        "  - Максимальная скорость (0 сек задержки)\n\n"
        "Режим 2 (3 кнопки):\n"
        "  - Полная автоматизация\n"
        "  - Нажатие всех кнопок последовательно\n\n"
        "💡 Управление сессиями:\n"
        "  - Запуск/остановка/перезагрузка\n"
        "  - Переключение режимов\n"
        "  - Просмотр статистики и логов\n\n"
        "📊 Мониторинг:\n"
        "  - Статус всех сессий в реальном времени\n"
        "  - Счетчики триггеров и ошибок\n"
        "  - Время работы\n"
    )

    keyboard = [
        [InlineKeyboardButton("« Назад в меню", callback_data="menu_main")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ==================== КОМАНДЫ ====================

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status"""
    if not await check_authorization(update, context):
        return

    statuses = manager.monitor_all_sessions()

    if not statuses:
        text = "Нет активных сессий"
    else:
        lines = []
        for status in statuses:
            emoji = get_status_emoji(status['status'])
            mode_name = get_mode_name(status['mode'])
            lines.append(
                f"{emoji} Сессия {status['session_id']}: {status['status'].upper()} | {mode_name}"
            )
        text = "📊 Статус сессий:\n\n" + "\n".join(lines)

    await update.message.reply_text(text)


async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /sessions"""
    if not await check_authorization(update, context):
        return

    sessions = db.get_all_sessions()

    if not sessions:
        text = "Нет зарегистрированных сессий"
    else:
        lines = []
        for session in sessions:
            masked_phone = mask_phone_number(session['phone_number'])
            lines.append(f"Сессия {session['id']}: {session['session_name']} ({masked_phone})")
        text = "📋 Список сессий:\n\n" + "\n".join(lines)

    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    if not await check_authorization(update, context):
        return

    text = (
        "📚 Справка по командам:\n\n"
        "/start - Главное меню\n"
        "/status - Статус всех сессий\n"
        "/sessions - Список сессий\n"
        "/help - Эта справка\n\n"
        "Для управления сессиями используйте /start"
    )

    await update.message.reply_text(text)


# ==================== ОБРАБОТЧИК CALLBACK ====================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Главный обработчик callback запросов"""
    query = update.callback_query
    data = query.data

    # Меню
    if data == "menu_main":
        await show_main_menu(update, context, edit=True)
    elif data == "menu_sessions":
        await menu_sessions(update, context)
    elif data == "menu_monitoring":
        await menu_monitoring(update, context)
    elif data == "menu_settings":
        await menu_settings(update, context)
    elif data == "menu_help":
        await menu_help(update, context)

    # Управление сессией
    elif data.startswith("session_"):
        parts = data.split("_")

        if len(parts) == 2:  # session_{id}
            session_id = int(parts[1])
            await show_session_control(update, context, session_id)

        elif parts[1] == "start":  # session_start_{id}
            session_id = int(parts[2])
            await session_start(update, context, session_id)

        elif parts[1] == "stop":  # session_stop_{id}
            session_id = int(parts[2])
            await session_stop(update, context, session_id)

        elif parts[1] == "restart":  # session_restart_{id}
            session_id = int(parts[2])
            await session_restart(update, context, session_id)

        elif parts[1] == "mode":  # session_mode_{mode}_{id} или session_mode_confirm_{id}_{mode}
            if parts[2] == "confirm":
                session_id = int(parts[3])
                new_mode = int(parts[4])
                await session_mode_confirm(update, context, session_id, new_mode)
            else:
                new_mode = int(parts[2])
                session_id = int(parts[3])
                await session_switch_mode(update, context, session_id, new_mode)

        elif parts[1] == "stats":  # session_stats_{id}
            session_id = int(parts[2])
            await show_session_stats(update, context, session_id)

        elif parts[1] == "logs":  # session_logs_{id}_{lines}
            session_id = int(parts[2])
            lines = int(parts[3]) if len(parts) > 3 else 20
            await show_session_logs(update, context, session_id, lines)


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

async def main():
    """Главная функция запуска бота"""
    logger.info("="*60)
    logger.info("Запуск Control Bot для управления автоматизацией")
    logger.info("="*60)

    # Создаем директории
    os.makedirs("logs", exist_ok=True)
    os.makedirs("sessions", exist_ok=True)

    # Создаем приложение
    application = Application.builder().token(CONTROL_BOT_TOKEN).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("sessions", sessions_command))
    application.add_handler(CommandHandler("help", help_command))

    # Регистрируем обработчик callback
    application.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("✓ Бот запущен и готов к работе")
    logger.info("="*60)

    # Запускаем бота
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n" + "="*60)
        logger.info("Остановка Control Bot...")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
