# Патч - помечать как обработанное ДО нажатия, а не после

with open('bot_automation.py', 'r') as f:
    content = f.read()

# В waiting_list: помечаем ДО нажатия
old_waiting_list_click = '''if '🚛' in button.text or button.text.replace(' ', '').replace('.', '').isdigit():
                                    logger.info(f"⚡ Выбираю перевозку: '{button.text}'")
                                    success = await self.click_button(button, "(первая перевозка)")
                                    if success:
                                        # Помечаем как обработанное
                                        self.last_processed_state_msg = state_msg_key
                                        # Переходим в следующее состояние
                                        self.automation_state = 'waiting_details'
                                        logger.info("✅ Шаг 2/3: Выбрана перевозка")
                                    return'''

new_waiting_list_click = '''if '🚛' in button.text or button.text.replace(' ', '').replace('.', '').isdigit():
                                    logger.info(f"⚡ Выбираю перевозку: '{button.text}'")
                                    # КРИТИЧНО: Помечаем ДО нажатия!
                                    self.last_processed_state_msg = state_msg_key
                                    success = await self.click_button(button, "(первая перевозка)")
                                    if success:
                                        # Переходим в следующее состояние
                                        self.automation_state = 'waiting_details'
                                        logger.info("✅ Шаг 2/3: Выбрана перевозка")
                                    return'''

content = content.replace(old_waiting_list_click, new_waiting_list_click)

# В waiting_details: тоже помечаем ДО нажатия
old_waiting_details_click = '''if keyword in button.text.lower():
                                        logger.info(f"✅ Нажимаю: '{button.text}'")
                                        success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.last_processed_state_msg = state_msg_key
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")
                                        return'''

new_waiting_details_click = '''if keyword in button.text.lower():
                                        logger.info(f"✅ Нажимаю: '{button.text}'")
                                        # КРИТИЧНО: Помечаем ДО нажатия!
                                        self.last_processed_state_msg = state_msg_key
                                        success = await self.click_button(button, "(БРОНИРОВАНИЕ)")
                                        if success:
                                            self.automation_state = None
                                            logger.info("🎉 БРОНИРОВАНИЕ ЗАВЕРШЕНО!")
                                        return'''

content = content.replace(old_waiting_details_click, new_waiting_details_click)

with open('bot_automation.py', 'w') as f:
    f.write(content)

print('✅ Патч против дублирования применён!')
