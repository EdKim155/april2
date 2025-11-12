# Финальный патч - правильная логика ожидания финальной клавиатуры

with open('bot_automation.py', 'r') as f:
    content = f.read()

# Заменить логику в waiting_list
old_waiting_list = '''            if self.automation_state == 'waiting_list':
                # Ждем список перевозок
                logger.info("📋 Получен список, выбираю первую перевозку...")
                await asyncio.sleep(0.15)  # Даем время финализироваться
                
                if self.last_keyboard and len(self.last_keyboard.rows) > 0:
                    for row in self.last_keyboard.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                logger.info(f"⚡ Выбираю перевозку: '{button.text}'")
                                success = await self.click_button(button, "(первая перевозка)")
                                if success:
                                    # Переходим в следующее состояние
                                    self.automation_state = 'waiting_details'
                                    logger.info("✅ Шаг 2/3: Выбрана перевозка")
                                return'''

new_waiting_list = '''            if self.automation_state == 'waiting_list':
                # Ждем список перевозок
                logger.info("📋 Получен список, выбираю первую перевозку...")
                await asyncio.sleep(0.15)  # Даем время финализироваться
                
                if self.last_keyboard and len(self.last_keyboard.rows) > 0:
                    # ВАЖНО: Ищем кнопку ПЕРЕВОЗКИ (с 🚛), а не кнопку меню
                    for row in self.last_keyboard.rows:
                        for button in row.buttons:
                            if isinstance(button, KeyboardButtonCallback):
                                # Проверяем что это кнопка перевозки, а не меню
                                if '🚛' in button.text or button.text.replace(' ', '').replace('.', '').isdigit():
                                    logger.info(f"⚡ Выбираю перевозку: '{button.text}'")
                                    success = await self.click_button(button, "(первая перевозка)")
                                    if success:
                                        # Переходим в следующее состояние
                                        self.automation_state = 'waiting_details'
                                        logger.info("✅ Шаг 2/3: Выбрана перевозка")
                                    return
                    # Если не нашли перевозку - это промежуточный edit, не помечаем как обработанное
                    logger.debug("⏸️  Нет кнопок перевозок, ждём финального edit")
                    return'''

content = content.replace(old_waiting_list, new_waiting_list)

# Также нужно НЕ помечать как обработанное если не нашли нужную кнопку
# Для этого переместим сохранение last_processed_state_msg
old_early_save = '''        # КРИТИЧЕСКИ ВАЖНО: Помечаем как обрабатываемое СРАЗУ!
        self.last_processed_state_msg = state_msg_key
        
        logger.info(f"🔄 Состояние: {self.automation_state}, сообщение: {message.id}")'''

new_early_save = '''        logger.info(f"🔄 Состояние: {self.automation_state}, сообщение: {message.id}")'''

content = content.replace(old_early_save, new_early_save)

# Теперь добавляем сохранение last_processed_state_msg после УСПЕШНОЙ обработки
# В waiting_list после успешного нажатия
content = content.replace(
    '''success = await self.click_button(button, "(первая перевозка)")
                                    if success:
                                        # Переходим в следующее состояние
                                        self.automation_state = 'waiting_details'
                                        logger.info("✅ Шаг 2/3: Выбрана перевозка")''',
    '''success = await self.click_button(button, "(первая перевозка)")
                                    if success:
                                        # Помечаем как обработанное
                                        self.last_processed_state_msg = state_msg_key
                                        # Переходим в следующее состояние
                                        self.automation_state = 'waiting_details'
                                        logger.info("✅ Шаг 2/3: Выбрана перевозка")'''
)

# В waiting_details тоже нужно пометить после успешного нажатия
content = content.replace(
    '''success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")''',
    '''success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.last_processed_state_msg = state_msg_key
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")'''
)

with open('bot_automation.py', 'w') as f:
    f.write(content)

print('✅ Финальный патч применён!')
