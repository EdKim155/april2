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
from telethon import TelegramClient, events
from telethon.tl.custom import Message
from telethon.tl.types import KeyboardButtonCallback, ReplyInlineMarkup
from telethon.tl import functions
from config import CONFIG

# Загрузка .env файла вручную
def load_env(env_file='.env'):
    """Загрузка переменных из .env файла"""
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Загружаем переменные окружения из .env
load_env()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, CONFIG.get('LOG_LEVEL', 'INFO'))
)
logger = logging.getLogger(__name__)

# Отключаем DEBUG логи от telethon
logging.getLogger('telethon').setLevel(logging.WARNING)

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

        # State Machine для многошаговой автоматизации
        self.automation_state = None  # None, 'waiting_list', 'waiting_details', 'waiting_confirm'
        self.automation_start_time = None

        # Защита от дубликатов при множественных edit сообщений
        self.last_processed_state_msg = None  # Формат: "message_id_state"

        self.stats = {
            'triggers_detected': 0,
            'buttons_clicked': 0,
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
        """Сохранение последней клавиатуры с кнопками"""
        if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
            self.last_keyboard = message.reply_markup
            self.last_message_id = message.id

            if CONFIG.get('LOG_BUTTONS', True):
                logger.info(f"Сохранена клавиатура с {len(message.reply_markup.rows)} рядами кнопок")
                # Логирование кнопок для отладки
                for row_idx, row in enumerate(message.reply_markup.rows):
                    buttons_text = [btn.text for btn in row.buttons if hasattr(btn, 'text')]
                    logger.debug(f"  Ряд {row_idx + 1}: {buttons_text}")

    async def find_button_by_keywords(self, keywords: List[str]) -> Optional[tuple]:
        """Поиск кнопки по ключевым словам"""
        if not self.last_keyboard:
            return None

        for row_idx, row in enumerate(self.last_keyboard.rows):
            for btn_idx, button in enumerate(row.buttons):
                if isinstance(button, KeyboardButtonCallback) and hasattr(button, 'text'):
                    for keyword in keywords:
                        if keyword.lower() in button.text.lower():
                            return (row_idx, btn_idx, button)
        return None

    async def click_button(self, button: KeyboardButtonCallback, button_info: str = "") -> bool:
        """Нажатие на конкретную кнопку"""
        if not self.last_message_id:
            logger.warning("Нет ID последнего сообщения")
            return False

        try:
            logger.info(f"⚡ Нажатие на кнопку: '{button.text}' {button_info}")

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

    async def continue_automation(self, message: Message):
        """Продолжение многошаговой автоматизации"""
        logger.info(f"🔄 Состояние: {self.automation_state}")

        # Защита от дубликатов: используем хеш кнопок чтобы различать редакции сообщения
        buttons_hash = ""
        if message.reply_markup and isinstance(message.reply_markup, ReplyInlineMarkup):
            button_texts = []
            for row in message.reply_markup.rows:
                for btn in row.buttons:
                    if isinstance(btn, KeyboardButtonCallback):
                        button_texts.append(btn.text)
            buttons_hash = "_".join(button_texts)

        state_key = f"{message.id}_{self.automation_state}_{hash(buttons_hash)}"
        if self.last_processed_state_msg == state_key:
            logger.debug(f"⏭️ Пропускаем дубликат: {state_key}")
            return
        self.last_processed_state_msg = state_key

        # Проверяем таймаут с учетом конфигурации
        if self.automation_start_time:
            timeout = CONFIG.get('AUTOMATION_TIMEOUT', 3.0)
            elapsed = (datetime.now() - self.automation_start_time).total_seconds()
            if elapsed > timeout:
                logger.warning(f"⏱️ Таймаут автоматизации ({elapsed:.2f}s > {timeout}s)")
                self.automation_state = None
                return

        try:
            if self.automation_state == 'waiting_list':
                # Получили список перевозок, выбираем первую
                logger.info("📋 Получен список перевозок, выбираю первую...")
                delay = CONFIG.get('DELAY_BETWEEN_CLICKS', 0.15)
                await asyncio.sleep(delay * 0.5)  # Половина задержки для быстроты

                if self.last_keyboard and len(self.last_keyboard.rows) > 0:
                    # Логируем все доступные кнопки
                    logger.info("🔍 Доступные кнопки в списке:")
                    for row_idx, row in enumerate(self.last_keyboard.rows):
                        for btn_idx, btn in enumerate(row.buttons):
                            if isinstance(btn, KeyboardButtonCallback):
                                logger.info(f"  [{row_idx},{btn_idx}] '{btn.text}'")

                    # Ищем кнопку с грузовиком 🚛 (это рейс)
                    truck_button = None
                    for row in self.last_keyboard.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                # Проверяем наличие эмодзи грузовика или цифр (ID рейса)
                                if '🚛' in button.text or any(char.isdigit() for char in button.text[:3]):
                                    truck_button = button
                                    break
                        if truck_button:
                            break

                    # Если нашли рейс - нажимаем на него
                    if truck_button:
                        logger.info(f"⚡ Выбираю перевозку с грузовиком: '{truck_button.text}'")
                        await self.click_button(truck_button, "(перевозка с 🚛)")
                        self.automation_state = 'waiting_details'
                        return

                    # Если не нашли грузовик - возможно это еще главное меню, пропускаем
                    logger.warning("⚠️ Не нашел кнопку с грузовиком 🚛 - возможно еще главное меню")
                    logger.warning("⚠️ Жду следующего обновления...")
                    # НЕ сбрасываем state, ждем следующего сообщения

            elif self.automation_state == 'waiting_details':
                # Получили детали перевозки, ищем кнопку подтверждения
                logger.info("📦 Получены детали, ищу кнопку подтверждения...")

                # ВАЖНО: Даём время клавиатуре обновиться
                # Telegram отправляет несколько edit событий, последнее - с правильной клавиатурой
                delay = CONFIG.get('DELAY_BETWEEN_CLICKS', 0.15)
                await asyncio.sleep(delay * 2)  # УВЕЛИЧЕННАЯ задержка для получения правильной клавиатуры

                if self.last_keyboard:
                    # Логируем ВСЕ кнопки для отладки
                    logger.info("🔍 Все доступные кнопки:")
                    all_buttons = []
                    has_truck = False
                    for row_idx, row in enumerate(self.last_keyboard.rows):
                        for btn_idx, button in enumerate(row.buttons):
                            if isinstance(button, KeyboardButtonCallback):
                                logger.info(f"  Кнопка [{row_idx},{btn_idx}]: '{button.text}'")
                                all_buttons.append((button, row_idx, btn_idx))
                                if '🚛' in button.text:
                                    has_truck = True

                    # Проверяем, что это НЕ список рейсов (должны быть детали)
                    if has_truck:
                        logger.warning("⚠️ Клавиатура всё ещё содержит грузовики 🚛 - это старая клавиатура!")
                        logger.warning("⚠️ Жду правильную клавиатуру с кнопкой подтверждения...")
                        # НЕ сбрасываем state, ждём следующего обновления
                        return

                    # СТРОГИЙ список ключевых слов для кнопки подтверждения (только длинные слова!)
                    keywords = [
                        'подтвердить', 'подтверждаю', 'подтверждение',
                        'забронировать', 'бронировать', 'бронирую', 'бронирование',
                        'взять перевозку', 'беру', 'взял',
                        'оформить', 'оформляю', 'оформление',
                        'занять', 'занимаю',
                        'согласен',
                        'confirm', 'book', 'accept'
                    ]

                    # Пытаемся найти кнопку по ключевым словам
                    found = False
                    for button, row_idx, btn_idx in all_buttons:
                        button_text_lower = button.text.lower()
                        for keyword in keywords:
                            if keyword in button_text_lower:
                                logger.info(f"✅ Нашел кнопку подтверждения: '{button.text}' (совпадение: '{keyword}')")
                                await self.click_button(button, f"(БРОНИРОВАНИЕ по слову '{keyword}')")
                                self.automation_state = None  # Завершаем
                                logger.info("🎉 АВТОМАТИЧЕСКОЕ БРОНИРОВАНИЕ ЗАВЕРШЕНО!")
                                found = True
                                return

                    # FALLBACK: Если не нашли по ключевым словам, нажимаем первую кнопку
                    # НО исключаем кнопки главного меню
                    if not found and all_buttons:
                        # Исключаем кнопки меню
                        menu_keywords = ['список', 'меню', 'настройки', 'возврат', 'назад']
                        for button, row_idx, btn_idx in all_buttons:
                            button_lower = button.text.lower()
                            is_menu = any(mk in button_lower for mk in menu_keywords)
                            if not is_menu:
                                logger.warning(f"⚠️ Кнопка подтверждения не найдена по ключевым словам!")
                                logger.warning(f"⚠️ Нажимаю первую НЕ-МЕНЮ кнопку: '{button.text}'")
                                await self.click_button(button, "(FALLBACK: первая не-меню кнопка)")
                                self.automation_state = None
                                logger.info("🎉 АВТОМАТИЧЕСКОЕ БРОНИРОВАНИЕ ЗАВЕРШЕНО (FALLBACK)")
                                found = True
                                return

                    if not found:
                        logger.error("❌ НЕТ ДОСТУПНЫХ КНОПОК ПОДТВЕРЖДЕНИЯ!")
                        self.automation_state = None

        except Exception as e:
            logger.error(f"❌ Ошибка в автоматизации: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.automation_state = None

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
        logger.info("="*60)

        try:
            delay = CONFIG.get('DELAY_AFTER_TRIGGER', 0.05)
            await asyncio.sleep(delay)

            # Используем сохраненную клавиатуру вместо отправки /start
            if self.last_keyboard:
                logger.info("💨 Использую сохраненную клавиатуру (БЫСТРЫЙ режим!)")
                logger.info("🤖 Запускаю многошаговую автоматизацию...")

                # Инициализируем State Machine
                self.automation_state = 'waiting_list'
                self.automation_start_time = datetime.now()

                # Нажимаем первую кнопку (Список перевозок)
                success = await self.click_buttons_by_strategy()

                if success:
                    logger.info("✅ Шаг 1/3: Открываю список перевозок")
                else:
                    logger.warning("⚠️  Не удалось нажать кнопки")
                    self.automation_state = None
            else:
                logger.info("📤 Нет сохраненной клавиатуры, отправляю /start")
                await self.send_start_command()

        except Exception as e:
            logger.error(f"❌ Ошибка при обработке новых перевозок: {e}")
            self.stats['errors'] += 1
            self.automation_state = None
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
                   f"Ошибок: {self.stats['errors']}, "
                   f"Время работы: {uptime}")

    async def handle_message(self, message):
        """Общая логика обработки сообщений"""
        # Проверяем, что сообщение от нужного бота
        if self.bot_entity and message.peer_id.user_id != self.bot_entity.id:
            return

        # Сохраняем все клавиатуры для последующего использования
        await self.save_keyboard(message)

        # Проверяем триггерное сообщение
        if message.text and TRIGGER_MESSAGE in message.text:
            await self.process_new_transport(message)
            return

        # Если идет автоматизация, продолжаем
        if self.automation_state:
            await self.continue_automation(message)

    async def handle_new_message(self, event):
        """Обработчик новых сообщений"""
        await self.handle_message(event.message)

    async def handle_edited_message(self, event):
        """Обработчик редактированных сообщений (для edit)"""
        logger.debug("📝 Сообщение обновлено (edit)")
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
        logger.info(f"⏱️  Задержка после триггера: {CONFIG.get('DELAY_AFTER_TRIGGER', 0.05)}с")
        logger.info("="*60)

        # Регистрация обработчиков (БЕЗ декоратора!)
        self.client.add_event_handler(
            self.handle_new_message,
            events.NewMessage()
        )
        self.client.add_event_handler(
            self.handle_edited_message,
            events.MessageEdited()
        )

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
