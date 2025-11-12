# Патч для bot_automation.py - сохранять last_processed_state_msg СРАЗУ

with open('bot_automation.py', 'r') as f:
    content = f.read()

# Найти функцию continue_automation и добавить раннее сохранение
old_code = '''    async def continue_automation(self, message: Message):
        """Продолжение многошаговой автоматизации"""
        
        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Проверяем комбинацию (message_id + state)
        state_msg_key = f"{message.id}_{self.automation_state}"
        if self.last_processed_state_msg == state_msg_key:
            logger.debug(f"⏭️  Пропускаем: {state_msg_key} уже обработан")
            return
        
        logger.info(f"🔄 Состояние: {self.automation_state}, сообщение: {message.id}")'''

new_code = '''    async def continue_automation(self, message: Message):
        """Продолжение многошаговой автоматизации"""
        
        # КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Проверяем комбинацию (message_id + state)
        state_msg_key = f"{message.id}_{self.automation_state}"
        if self.last_processed_state_msg == state_msg_key:
            logger.debug(f"⏭️  Пропускаем: {state_msg_key} уже обработан")
            return
        
        # КРИТИЧЕСКИ ВАЖНО: Помечаем как обрабатываемое СРАЗУ!
        self.last_processed_state_msg = state_msg_key
        
        logger.info(f"🔄 Состояние: {self.automation_state}, сообщение: {message.id}")'''

content = content.replace(old_code, new_code)

# Теперь убрать сохранение last_processed_state_msg после успешного нажатия
# (оно больше не нужно)
content = content.replace(
    '''success = await self.click_button(button, "(первая перевозка)")
                                if success:
                                    # Помечаем как обработанное
                                    self.last_processed_state_msg = state_msg_key
                                    # Переходим в следующее состояние
                                    self.automation_state = 'waiting_details'
                                    logger.info("✅ Шаг 2/3: Выбрана перевозка")''',
    '''success = await self.click_button(button, "(первая перевозка)")
                                if success:
                                    # Переходим в следующее состояние
                                    self.automation_state = 'waiting_details'
                                    logger.info("✅ Шаг 2/3: Выбрана перевозка")'''
)

content = content.replace(
    '''success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.last_processed_state_msg = state_msg_key
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")''',
    '''success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")'''
)

with open('bot_automation.py', 'w') as f:
    f.write(content)

print('✅ Патч применён!')
