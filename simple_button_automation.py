#!/usr/bin/env python3
"""
Упрощенная автоматизация: нажатие только на кнопку "🔔Список прямых перевозок"
При появлении триггера "Появились новые перевозки" нажимается кнопка и ничего больше.
"""
import os
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from telethon.tl import functions

# ============================================================================
# КОНФИГУРАЦИЯ - ОБНОВЛЕННЫЕ CREDENTIALS
# ============================================================================
API_ID = 24101164
API_HASH = '80cc2adcd452008ae630d0ee778b5122'
PHONE_NUMBER = '+79512586335'
BOT_USERNAME = '@ACarriers_bot'
SESSION_NAME = 'simple_automation_session'

# Триггер для активации
TRIGGER_MESSAGE = 'Появились новые перевозки'

# Текст кнопки для нажатия
TARGET_BUTTON_TEXT = '🔔Список прямых перевозок'

# Задержка после обнаружения триггера (секунды) - УБРАНА ДЛЯ МГНОВЕННОЙ РЕАКЦИИ
DELAY_AFTER_TRIGGER = 0

# ============================================================================
# ЛОГИРОВАНИЕ
# ============================================================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('telethon').setLevel(logging.WARNING)


class SimpleButtonBot:
    """Бот для автоматического нажатия на конкретную кнопку при триггере"""

    def __init__(self):
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
        """Инициализация клиента Telegram"""
        logger.info('🔧 Инициализация...')
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await self.client.start(phone=PHONE_NUMBER)
        logger.info('✓ Подключено к Telegram')

        if BOT_USERNAME:
            try:
                self.bot_entity = await self.client.get_entity(BOT_USERNAME)
                logger.info(f'✓ Подключен к боту: {BOT_USERNAME}')
            except Exception as e:
                logger.error(f'❌ Ошибка подключения к боту: {e}')

    async def save_keyboard(self, message: Message):
        """Сохранение клавиатуры из сообщения"""
        if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
            self.last_keyboard = message.reply_markup
            self.last_message_id = message.id

            # Логируем доступные кнопки
            button_texts = []
            for row in self.last_keyboard.rows:
                for button in row.buttons:
                    if isinstance(button, KeyboardButtonCallback):
                        button_texts.append(button.text)
            logger.info(f'💾 Сохранена клавиатура с кнопками: {button_texts}')

    async def click_button(self, button: KeyboardButtonCallback) -> bool:
        """Нажатие на кнопку"""
        if not self.last_message_id:
            logger.warning('⚠️ Нет ID последнего сообщения')
            return False

        try:
            logger.info(f'⚡ Нажатие на кнопку: "{button.text}"')
            await self.client(
                functions.messages.GetBotCallbackAnswerRequest(
                    peer=self.bot_entity,
                    msg_id=self.last_message_id,
                    data=button.data
                )
            )
            logger.info(f'✅ Успешно нажата кнопка: "{button.text}"')
            self.stats['buttons_clicked'] += 1
            return True

        except Exception as e:
            logger.error(f'❌ Ошибка при нажатии кнопки: {e}')
            self.stats['errors'] += 1
            return False

    async def find_and_click_target_button(self):
        """Поиск и нажатие на целевую кнопку"""
        if not self.last_keyboard:
            logger.warning('⚠️ Клавиатура не сохранена')
            return False

        # Ищем кнопку с нужным текстом (точное совпадение или содержит ключевые слова)
        for row in self.last_keyboard.rows:
            for button in row.buttons:
                if isinstance(button, KeyboardButtonCallback):
                    # Точное совпадение
                    if button.text == TARGET_BUTTON_TEXT:
                        logger.info(f'🎯 Найдена целевая кнопка (точное совпадение): "{button.text}"')
                        return await self.click_button(button)

                    # Проверка на содержание ключевых слов (гибкий поиск)
                    if ('🔔' in button.text and
                        'прямых' in button.text.lower() and
                        'перевозок' in button.text.lower()):
                        logger.info(f'🎯 Найдена целевая кнопка (похожая): "{button.text}"')
                        return await self.click_button(button)

        logger.warning(f'⚠️ Кнопка "{TARGET_BUTTON_TEXT}" не найдена в клавиатуре')
        logger.warning(f'💡 Доступные кнопки:')
        for row in self.last_keyboard.rows:
            for button in row.buttons:
                if isinstance(button, KeyboardButtonCallback):
                    logger.warning(f'   - "{button.text}"')
        return False

    async def process_trigger(self, message: Message):
        """Обработка триггера - МГНОВЕННАЯ РЕАКЦИЯ"""
        if self.is_processing:
            return

        self.is_processing = True
        self.stats['triggers_detected'] += 1

        try:
            logger.info(f'🚨 ТРИГГЕР #{self.stats["triggers_detected"]}! Нажимаю кнопку...')

            # МГНОВЕННОЕ нажатие без задержек
            if DELAY_AFTER_TRIGGER > 0:
                await asyncio.sleep(DELAY_AFTER_TRIGGER)

            # Нажимаем кнопку
            success = await self.find_and_click_target_button()

            if success:
                logger.info(f'✅ Кнопка нажата! (Триггеров: {self.stats["triggers_detected"]}, Нажатий: {self.stats["buttons_clicked"]}, Ошибок: {self.stats["errors"]})')
            else:
                logger.warning('⚠️ Не удалось нажать кнопку')

        finally:
            self.is_processing = False

    def print_stats(self):
        """Вывод статистики"""
        runtime = datetime.now() - self.stats['start_time']
        logger.info('─' * 70)
        logger.info('📊 СТАТИСТИКА:')
        logger.info(f'   • Триггеров обнаружено: {self.stats["triggers_detected"]}')
        logger.info(f'   • Кнопок нажато: {self.stats["buttons_clicked"]}')
        logger.info(f'   • Ошибок: {self.stats["errors"]}')
        logger.info(f'   • Время работы: {str(runtime).split(".")[0]}')
        logger.info('─' * 70)

    async def handle_message(self, message: Message):
        """Обработчик сообщений - ОПТИМИЗИРОВАН ДЛЯ СКОРОСТИ"""
        # Сохраняем клавиатуру из любого сообщения
        await self.save_keyboard(message)

        # Проверяем на триггер - ПРИОРИТЕТ #1
        if message.text and TRIGGER_MESSAGE in message.text:
            await self.process_trigger(message)

    async def run(self):
        """Запуск бота"""
        await self.initialize()

        logger.info('=' * 70)
        logger.info('🤖 УПРОЩЕННЫЙ БОТ ЗАПУЩЕН')
        logger.info(f'🎯 Триггер: "{TRIGGER_MESSAGE}"')
        logger.info(f'🔘 Целевая кнопка: "{TARGET_BUTTON_TEXT}"')
        logger.info('=' * 70)

        # Подписываемся на события - ТОЛЬКО ОТ БОТА для скорости
        if self.bot_entity:
            self.client.add_event_handler(
                lambda e: self.handle_message(e.message),
                events.NewMessage(chats=[self.bot_entity])
            )
            self.client.add_event_handler(
                lambda e: self.handle_message(e.message),
                events.MessageEdited(chats=[self.bot_entity])
            )
        else:
            # Fallback если бот не найден
            self.client.add_event_handler(
                lambda e: self.handle_message(e.message),
                events.NewMessage()
            )
            self.client.add_event_handler(
                lambda e: self.handle_message(e.message),
                events.MessageEdited()
            )

        # Запускаем бота
        await self.client.run_until_disconnected()


if __name__ == '__main__':
    try:
        asyncio.run(SimpleButtonBot().run())
    except KeyboardInterrupt:
        logger.info('\n👋 Остановка бота...')
    except Exception as e:
        logger.error(f'❌ Критическая ошибка: {e}', exc_info=True)
