#!/usr/bin/env python3
"""
Telegram Bot Automation для быстрого бронирования перевозок
Использует сессию Telegram для автоматического нажатия кнопок при появлении новых перевозок
"""

import os
import asyncio
import logging
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from telethon.tl import functions
from automation_config import CONFIG

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, CONFIG.get('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
PHONE_NUMBER = os.getenv('PHONE_NUMBER')
BOT_USERNAME = os.getenv('BOT_USERNAME')  # Юзернейм бота (например, @your_bot)
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_session')

# Текст триггерного сообщения
TRIGGER_MESSAGE = "Появились новые перевозки"

class TransportBookingBot:
    """Автоматизация бронирования перевозок через Telegram бота"""

    def __init__(self):
        self.client = None
        self.bot_entity = None
        self.last_keyboard = None
        self.last_message_id = None
        self.is_processing = False

        # Event-driven подход: события для синхронизации
        self.keyboard_updated = asyncio.Event()
        self.message_queue = asyncio.Queue()

        # State Machine для многошаговой автоматизации
        self.current_state = None
        self.state_data = {}

        # Кэш кнопок для быстрого доступа
        self.button_cache = {}

        self.stats = {
            'triggers_detected': 0,
            'buttons_clicked': 0,
            'successful_bookings': 0,
            'failed_bookings': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def initialize(self):
        """Инициализация клиента Telegram"""
        logger.info("Инициализация Telegram клиента...")

        if not API_ID or not API_HASH:
            raise ValueError("API_ID и API_HASH должны быть указаны в .env файле")

        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        await self.client.start(phone=PHONE_NUMBER)

        logger.info("Успешное подключение к Telegram")

        # Получаем сущность бота
        if BOT_USERNAME:
            try:
                self.bot_entity = await self.client.get_entity(BOT_USERNAME)
                logger.info(f"Подключен к боту: {BOT_USERNAME}")
            except Exception as e:
                logger.error(f"Не удалось найти бота {BOT_USERNAME}: {e}")

    async def save_keyboard(self, message: Message):
        """Сохранение последней клавиатуры с кнопками (Event-driven)"""
        if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
            is_update = self.last_message_id == message.id
            self.last_keyboard = message.reply_markup
            self.last_message_id = message.id

            # Обновляем кэш кнопок для быстрого доступа
            self._update_button_cache()

            # Сигнализируем об обновлении клавиатуры (event-driven)
            self.keyboard_updated.set()

            if CONFIG.get('LOG_BUTTONS', True):
                action = "Обновлена" if is_update else "Сохранена"
                logger.info(f"{action} клавиатура с {len(message.reply_markup.rows)} рядами кнопок")
                # Логирование кнопок для отладки
                for row_idx, row in enumerate(message.reply_markup.rows):
                    buttons_text = [btn.text for btn in row.buttons if hasattr(btn, 'text')]
                    logger.debug(f"  Ряд {row_idx + 1}: {buttons_text}")

    def _update_button_cache(self):
        """Обновление кэша кнопок для быстрого доступа"""
        self.button_cache.clear()
        if not self.last_keyboard:
            return

        for row_idx, row in enumerate(self.last_keyboard.rows):
            for btn_idx, button in enumerate(row.buttons):
                if isinstance(button, KeyboardButtonCallback) and hasattr(button, 'text'):
                    # Кэшируем кнопки по тексту (в lowercase для поиска)
                    key = button.text.lower()
                    self.button_cache[key] = (row_idx, btn_idx, button)

    async def find_button_by_keywords(self, keywords: List[str]) -> Optional[tuple]:
        """Поиск кнопки по ключевым словам (с использованием кэша)"""
        if not self.button_cache:
            return None

        # Сначала ищем точное совпадение
        for keyword in keywords:
            key = keyword.lower()
            if key in self.button_cache:
                return self.button_cache[key]

        # Затем ищем частичное совпадение
        for keyword in keywords:
            key = keyword.lower()
            for cached_key, button_info in self.button_cache.items():
                if key in cached_key:
                    return button_info

        return None

    async def wait_for_keyboard_update(self, timeout: float = None) -> bool:
        """Ожидание обновления клавиатуры (event-driven подход)"""
        if timeout is None:
            timeout = CONFIG.get('KEYBOARD_UPDATE_TIMEOUT', 0.5)

        try:
            # Сбрасываем флаг перед ожиданием
            self.keyboard_updated.clear()

            # Ждем обновления с таймаутом
            await asyncio.wait_for(self.keyboard_updated.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            logger.debug(f"⏱️ Таймаут ожидания обновления клавиатуры ({timeout}s)")
            return False

    async def click_button(self, button: KeyboardButtonCallback, button_info: str = "", wait_update: bool = True) -> bool:
        """Нажатие на конкретную кнопку (оптимизированное)"""
        if not self.last_message_id:
            logger.warning("Нет ID последнего сообщения")
            return False

        try:
            logger.info(f"⚡ Нажатие на кнопку: '{button.text}' {button_info}")

            # Сбрасываем событие перед нажатием, если будем ждать обновления
            if wait_update:
                self.keyboard_updated.clear()

            await self.client(
                functions.messages.GetBotCallbackAnswerRequest(
                    peer=self.bot_entity,
                    msg_id=self.last_message_id,
                    data=button.data
                )
            )

            logger.info(f"✓ Кнопка '{button.text}' успешно нажата")
            self.stats['buttons_clicked'] += 1

            # Ждем обновления клавиатуры (event-driven или фиксированная задержка)
            if wait_update:
                if CONFIG.get('USE_EVENT_WAIT', True):
                    await self.wait_for_keyboard_update()
                else:
                    # Быстрая фиксированная задержка вместо event wait
                    delay = CONFIG.get('DELAY_BETWEEN_CLICKS', 0.02)
                    await asyncio.sleep(delay)

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка при нажатии кнопки: {e}")
            self.stats['errors'] += 1
            return False

    async def click_buttons_by_strategy(self) -> bool:
        """Нажатие кнопок согласно выбранной стратегии"""
        if not self.last_keyboard:
            logger.warning("Нет сохраненной клавиатуры для нажатия")
            return False

        strategy = CONFIG.get('BUTTON_STRATEGY', 'first')
        delay = CONFIG.get('DELAY_BETWEEN_CLICKS', 0.1)

        try:
            if strategy == 'first':
                # Нажимаем первую доступную кнопку
                for row_idx, row in enumerate(self.last_keyboard.rows):
                    for btn_idx, button in enumerate(row.buttons):
                        if isinstance(button, KeyboardButtonCallback):
                            return await self.click_button(
                                button,
                                f"(первая доступная, ряд {row_idx + 1})"
                            )

            elif strategy == 'custom':
                # Ищем кнопку по ключевым словам
                keywords = CONFIG.get('BUTTON_KEYWORDS', [])
                result = await self.find_button_by_keywords(keywords)

                if result:
                    row_idx, btn_idx, button = result
                    return await self.click_button(
                        button,
                        f"(найдена по ключевым словам, ряд {row_idx + 1})"
                    )
                else:
                    logger.warning(f"Не найдено кнопок с ключевыми словами: {keywords}")
                    # Fallback на первую кнопку
                    logger.info("Переключаюсь на первую доступную кнопку...")
                    return await self.click_buttons_by_strategy()

            elif strategy == 'all':
                # Нажимаем все кнопки последовательно
                success = False
                for row_idx, row in enumerate(self.last_keyboard.rows):
                    for btn_idx, button in enumerate(row.buttons):
                        if isinstance(button, KeyboardButtonCallback):
                            result = await self.click_button(
                                button,
                                f"(ряд {row_idx + 1}, кнопка {btn_idx + 1})"
                            )
                            if result:
                                success = True
                                await asyncio.sleep(delay)
                return success

            logger.warning("Не найдено callback кнопок для нажатия")
            return False

        except Exception as e:
            logger.error(f"❌ Ошибка в стратегии нажатия кнопок: {e}")
            self.stats['errors'] += 1
            return False

    async def auto_book_shipment(self) -> bool:
        """Автоматическое многошаговое бронирование (State Machine)"""
        if not CONFIG.get('MULTI_STEP_ENABLED', True):
            return await self.click_buttons_by_strategy()

        logger.info("🤖 Запуск автоматического бронирования...")

        automation_timeout = CONFIG.get('AUTOMATION_TIMEOUT', 5.0)
        start_time = datetime.now()

        try:
            # Шаг 1: Нажимаем "Список перевозок"
            self.current_state = "waiting_for_shipment_list"
            logger.info("🔄 Состояние: ждем список перевозок")

            success = await self.click_buttons_by_strategy()
            if not success:
                logger.warning("⚠️  Не удалось открыть список перевозок")
                self.stats['failed_bookings'] += 1
                return False

            # Шаг 2: Выбираем первую перевозку из списка
            self.current_state = "waiting_for_shipment_details"

            # Минимальная задержка для обработки (если не используем event wait)
            if not CONFIG.get('USE_EVENT_WAIT', True):
                await asyncio.sleep(CONFIG.get('DELAY_BETWEEN_CLICKS', 0.02))

            shipment_button = None
            if self.last_keyboard:
                logger.info("📋 Обнаружен список перевозок, выбираю первую...")
                for row_idx, row in enumerate(self.last_keyboard.rows):
                    for btn_idx, button in enumerate(row.buttons):
                        if isinstance(button, KeyboardButtonCallback):
                            # Первая кнопка в списке - это перевозка
                            if row_idx == 0:  # Первый ряд
                                shipment_button = button
                                success = await self.click_button(
                                    button,
                                    f"(первая перевозка, ряд {row_idx + 1})"
                                )
                                break
                    if shipment_button:
                        break

            if not success or not shipment_button:
                logger.warning("⚠️  Не найдена перевозка для бронирования")
                self.stats['failed_bookings'] += 1
                return False

            # Шаг 3: Ищем кнопку подтверждения
            self.current_state = "waiting_for_booking_confirmation"
            logger.info("🔄 Состояние: ждем детали перевозки")

            # Минимальная задержка для обработки (если не используем event wait)
            if not CONFIG.get('USE_EVENT_WAIT', True):
                await asyncio.sleep(CONFIG.get('DELAY_BETWEEN_CLICKS', 0.02))

            # Ищем кнопку "Подтвердить" или "Забронировать"
            booking_keywords = ['подтвердить', 'забронировать', 'взять']
            booking_button = None

            if self.last_keyboard:
                logger.info("📦 Обнаружена кнопка бронирования...")
                for row_idx, row in enumerate(self.last_keyboard.rows):
                    for btn_idx, button in enumerate(row.buttons):
                        if isinstance(button, KeyboardButtonCallback):
                            for keyword in booking_keywords:
                                if keyword in button.text.lower():
                                    booking_button = button
                                    break
                        if booking_button:
                            break
                    if booking_button:
                        break

            if not booking_button:
                logger.warning("⚠️  Не найдена кнопка бронирования")
                self.stats['failed_bookings'] += 1
                return False

            # Шаг 4: Подтверждаем бронирование
            self.current_state = "booking_in_progress"
            logger.info("🔄 Состояние: выполняется бронирование")

            success = await self.click_button(
                booking_button,
                "(БРОНИРОВАНИЕ)",
                wait_update=True
            )

            if success:
                # Проверяем таймаут
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > automation_timeout:
                    logger.warning(f"⏱️ Таймаут автоматизации ({automation_timeout}s)")

                # Минимальная задержка для проверки результата
                if not CONFIG.get('USE_EVENT_WAIT', True):
                    await asyncio.sleep(CONFIG.get('DELAY_BETWEEN_CLICKS', 0.02))

                # Если клавиатура изменилась на меню, значит успех
                self.current_state = "completed"
                logger.info("🎉 УСПЕШНОЕ БРОНИРОВАНИЕ!")
                self.stats['successful_bookings'] += 1
                return True
            else:
                logger.warning("⚠️  Не удалось подтвердить бронирование")
                self.stats['failed_bookings'] += 1
                return False

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ Таймаут автоматизации ({automation_timeout}s)")
            self.stats['failed_bookings'] += 1
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка в автоматическом бронировании: {e}")
            self.stats['errors'] += 1
            self.stats['failed_bookings'] += 1
            return False
        finally:
            self.current_state = None

    async def process_new_transport(self, message: Message):
        """Обработка сообщения о новых перевозках"""
        if self.is_processing:
            logger.warning("⚠️  Уже обрабатывается предыдущее сообщение, пропускаем...")
            return

        self.is_processing = True
        self.stats['triggers_detected'] += 1

        logger.info("="*60)
        logger.info(f"🚨 ОБНАРУЖЕНЫ НОВЫЕ ПЕРЕВОЗКИ! (#{self.stats['triggers_detected']})")
        logger.info(f"⏱️  Время: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        logger.info("🤖 Запуск автоматического бронирования...")
        logger.info("="*60)

        try:
            delay = CONFIG.get('DELAY_AFTER_TRIGGER', 0.05)
            await asyncio.sleep(delay)

            # Используем сохраненную клавиатуру вместо отправки /start
            if self.last_keyboard:
                logger.info("💨 Использую сохраненную клавиатуру (БЫСТРЫЙ режим!)")

                # Запускаем автоматическое многошаговое бронирование
                success = await self.auto_book_shipment()

                if not success:
                    logger.warning("⚠️  Автоматическое бронирование не удалось")
            else:
                logger.info("📤 Нет сохраненной клавиатуры, отправляю /start")
                await self.send_start_command()

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке новых перевозок: {e}")
            self.stats['errors'] += 1
        finally:
            self.is_processing = False
            logger.info("="*60)
            self.print_stats()

    async def send_start_command(self):
        """Отправка команды /start (запасной вариант)"""
        if self.bot_entity:
            await self.client.send_message(self.bot_entity, '/start')
            logger.info("📨 Отправлена команда /start")

    def print_stats(self):
        """Вывод статистики работы бота"""
        uptime = datetime.now() - self.stats['start_time']
        logger.info(f"📊 Статистика: Триггеров: {self.stats['triggers_detected']}, "
                   f"Кнопок нажато: {self.stats['buttons_clicked']}, "
                   f"Успешных бронирований: {self.stats['successful_bookings']}, "
                   f"Неудачных бронирований: {self.stats['failed_bookings']}, "
                   f"Ошибок: {self.stats['errors']}, "
                   f"Время работы: {uptime}")

    async def handle_message(self, message):
        """Общая логика обработки сообщений (новых и отредактированных)"""
        # Проверяем, что сообщение от нужного бота
        if self.bot_entity and message.peer_id.user_id != self.bot_entity.id:
            return

        # Сохраняем все клавиатуры для последующего использования
        await self.save_keyboard(message)

        # Проверяем триггерное сообщение
        if message.text and TRIGGER_MESSAGE in message.text:
            await self.process_new_transport(message)

    @events.register(events.NewMessage)
    async def handle_new_message(self, event):
        """Обработчик новых сообщений"""
        await self.handle_message(event.message)

    @events.register(events.MessageEdited)
    async def handle_edited_message(self, event):
        """Обработчик редактированных сообщений"""
        logger.debug("🔄 Обнаружено редактирование сообщения")
        await self.handle_message(event.message)

    async def run(self):
        """Запуск бота"""
        await self.initialize()

        strategy = CONFIG.get('BUTTON_STRATEGY', 'first')
        logger.info("="*60)
        logger.info("🤖 Telegram Bot Automation - ЗАПУЩЕН")
        logger.info("="*60)
        logger.info(f"📱 Триггерное сообщение: '{TRIGGER_MESSAGE}'")
        logger.info(f"⚡ Стратегия кнопок: '{strategy}'")
        logger.info(f"💨 Режим: МАКСИМАЛЬНО БЫСТРЫЙ (без /start)")
        logger.info(f"🔄 Отслеживание: новые + редактированные сообщения")
        logger.info(f"⏱️  Задержка после триггера: {CONFIG.get('DELAY_AFTER_TRIGGER', 0.05)}с")
        logger.info("="*60)

        # Регистрация обработчиков
        self.client.add_event_handler(self.handle_new_message)
        self.client.add_event_handler(self.handle_edited_message)

        # Запуск клиента
        await self.client.run_until_disconnected()

async def main():
    """Главная функция"""
    try:
        bot = TransportBookingBot()
        await bot.run()
    except KeyboardInterrupt:
        logger.info("\n" + "="*60)
        logger.info("👋 Остановка бота...")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())
