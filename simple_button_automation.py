#!/usr/bin/env python3
"""
Режим 1: Простая автоматизация (Одна кнопка)
Быстрое нажатие ТОЛЬКО кнопки "Список прямых перевозок" при появлении триггера
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional
from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from telethon.tl import functions

# Настройка логирования
def setup_logging(session_id: int = 1):
    """Настройка логирования в файл и консоль"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"automation_{session_id}_{datetime.now().strftime('%Y-%m-%d')}.log")

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


class SimpleButtonAutomation:
    """
    Режим 1: Автоматизация с одной кнопкой
    Максимально быстрое нажатие целевой кнопки
    """

    def __init__(self, api_id: int, api_hash: str, phone_number: str,
                 session_file: str, bot_username: str,
                 trigger_message: str = "Появились новые перевозки",
                 target_button_text: str = "Список прямых перевозок",
                 delay_after_trigger: float = 0.0):
        """
        Инициализация автоматизации

        Args:
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            phone_number: Номер телефона
            session_file: Путь к файлу сессии
            bot_username: Username бота (@ACarriers_bot)
            trigger_message: Текст триггерного сообщения
            target_button_text: Текст целевой кнопки
            delay_after_trigger: Задержка после триггера (секунды)
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_file = session_file
        self.bot_username = bot_username
        self.trigger_message = trigger_message
        self.target_button_text = target_button_text
        self.delay_after_trigger = delay_after_trigger

        self.client = None
        self.bot_entity = None
        self.last_keyboard = None
        self.last_message_id = None
        self.is_processing = False

        # Статистика
        self.stats = {
            'triggers_detected': 0,
            'buttons_clicked': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def initialize(self):
        """Инициализация Telegram клиента"""
        logger.info("="*60)
        logger.info("Инициализация Telegram клиента (Режим 1)...")
        logger.info("="*60)

        self.client = TelegramClient(self.session_file, self.api_id, self.api_hash)
        await self.client.start(phone=self.phone_number)

        logger.info("✓ Успешное подключение к Telegram")

        # Получаем сущность бота
        try:
            self.bot_entity = await self.client.get_entity(self.bot_username)
            logger.info(f"✓ Подключен к боту: {self.bot_username}")
        except Exception as e:
            logger.error(f"❌ Не удалось найти бота {self.bot_username}: {e}")
            raise

    async def save_keyboard(self, message: Message):
        """Сохранение последней клавиатуры"""
        if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
            self.last_keyboard = message.reply_markup
            self.last_message_id = message.id
            logger.debug(f"Сохранена клавиатура с {len(message.reply_markup.rows)} рядами кнопок")

    async def find_target_button(self) -> Optional[KeyboardButtonCallback]:
        """Поиск целевой кнопки"""
        if not self.last_keyboard:
            return None

        for row in self.last_keyboard.rows:
            for button in row.buttons:
                if isinstance(button, KeyboardButtonCallback) and hasattr(button, 'text'):
                    if self.target_button_text.lower() in button.text.lower():
                        return button
        return None

    async def click_button(self, button: KeyboardButtonCallback) -> bool:
        """Нажатие кнопки"""
        if not self.last_message_id:
            logger.warning("Нет ID последнего сообщения")
            return False

        try:
            logger.info(f"⚡ Нажатие кнопки: '{button.text}'")

            await self.client(
                functions.messages.GetBotCallbackAnswerRequest(
                    peer=self.bot_entity,
                    msg_id=self.last_message_id,
                    data=button.data
                )
            )

            logger.info(f"✓ Кнопка '{button.text}' успешно нажата")
            self.stats['buttons_clicked'] += 1
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка при нажатии кнопки: {e}")
            self.stats['errors'] += 1
            return False

    async def process_trigger(self, message: Message):
        """Обработка триггерного сообщения"""
        if self.is_processing:
            logger.warning("⚠️  Уже обрабатывается предыдущий триггер, пропускаем...")
            return

        self.is_processing = True
        self.stats['triggers_detected'] += 1

        logger.info("="*60)
        logger.info(f"🚨 ТРИГГЕР ОБНАРУЖЕН! (#{self.stats['triggers_detected']})")
        logger.info(f"⏱️  Время: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        logger.info("="*60)

        try:
            # Минимальная задержка (если указана)
            if self.delay_after_trigger > 0:
                await asyncio.sleep(self.delay_after_trigger)

            # Ищем и нажимаем целевую кнопку
            if self.last_keyboard:
                button = await self.find_target_button()

                if button:
                    success = await self.click_button(button)
                    if success:
                        logger.info("✅ Кнопка успешно нажата")
                    else:
                        logger.warning("⚠️  Не удалось нажать кнопку")
                else:
                    logger.warning(f"⚠️  Целевая кнопка '{self.target_button_text}' не найдена")
                    self.stats['errors'] += 1
            else:
                logger.warning("⚠️  Нет сохраненной клавиатуры")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке триггера: {e}")
            self.stats['errors'] += 1
        finally:
            self.is_processing = False
            logger.info("="*60)
            self.print_stats()

    def print_stats(self):
        """Вывод статистики"""
        uptime = datetime.now() - self.stats['start_time']
        logger.info(f"📊 Статистика: Триггеров: {self.stats['triggers_detected']}, "
                   f"Кнопок: {self.stats['buttons_clicked']}, "
                   f"Ошибок: {self.stats['errors']}, "
                   f"Время работы: {uptime}")

    @events.register(events.NewMessage)
    async def handle_new_message(self, event):
        """Обработчик новых сообщений"""
        message = event.message

        # Проверка, что сообщение от нужного бота
        if self.bot_entity and message.peer_id.user_id != self.bot_entity.id:
            return

        # Сохраняем клавиатуру
        await self.save_keyboard(message)

        # Проверяем триггерное сообщение
        if message.text and self.trigger_message in message.text:
            await self.process_trigger(message)

    async def run(self):
        """Запуск автоматизации"""
        await self.initialize()

        logger.info("="*60)
        logger.info("🤖 РЕЖИМ 1: Автоматизация с ОДНОЙ кнопкой - ЗАПУЩЕН")
        logger.info("="*60)
        logger.info(f"📱 Триггерное сообщение: '{self.trigger_message}'")
        logger.info(f"🎯 Целевая кнопка: '{self.target_button_text}'")
        logger.info(f"⚡ Задержка после триггера: {self.delay_after_trigger}с")
        logger.info(f"💨 Режим: МАКСИМАЛЬНАЯ СКОРОСТЬ")
        logger.info("="*60)

        # Регистрация обработчика
        self.client.add_event_handler(self.handle_new_message)

        # Запуск клиента
        await self.client.run_until_disconnected()


async def main():
    """Главная функция"""
    # Параметры из аргументов командной строки или переменных окружения
    if len(sys.argv) < 7:
        logger.error("Недостаточно аргументов!")
        logger.error("Использование: python simple_button_automation.py <api_id> <api_hash> "
                    "<phone_number> <session_file> <bot_username> <session_id>")
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    phone_number = sys.argv[3]
    session_file = sys.argv[4]
    bot_username = sys.argv[5]
    session_id = int(sys.argv[6])

    # Дополнительные параметры (опционально)
    trigger_message = sys.argv[7] if len(sys.argv) > 7 else "Появились новые перевозки"
    target_button = sys.argv[8] if len(sys.argv) > 8 else "Список прямых перевозок"
    delay = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0

    try:
        bot = SimpleButtonAutomation(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            session_file=session_file,
            bot_username=bot_username,
            trigger_message=trigger_message,
            target_button_text=target_button,
            delay_after_trigger=delay
        )
        await bot.run()
    except KeyboardInterrupt:
        logger.info("\n" + "="*60)
        logger.info("👋 Остановка автоматизации...")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Настройка логирования
    session_id = int(sys.argv[6]) if len(sys.argv) > 6 else 1
    logger = setup_logging(session_id)

    # Запуск
    asyncio.run(main())
