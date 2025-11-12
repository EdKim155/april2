#!/usr/bin/env python3
"""
Менеджер сессий автоматизации
Управление запуском, остановкой и мониторингом процессов автоматизации
"""

import os
import sys
import signal
import subprocess
import logging
import psutil
import time
import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from database import get_database

logger = logging.getLogger(__name__)


class SessionManager:
    """Управление сессиями автоматизации"""

    def __init__(self):
        self.db = get_database()
        self.base_dir = Path(__file__).parent
        self.mode1_script = self.base_dir / "simple_button_automation.py"
        self.mode2_script = self.base_dir / "bot_automation.py"

    def start_session(self, session_id: int) -> bool:
        """
        Запустить сессию автоматизации

        Args:
            session_id: ID сессии

        Returns:
            True если успешно запущена
        """
        try:
            # Получаем данные сессии
            session = self.db.get_session(session_id)
            if not session:
                logger.error(f"Сессия {session_id} не найдена")
                return False

            # Проверяем, не запущена ли уже
            if session['status'] == 'running' and session['pid']:
                if self.is_process_running(session['pid']):
                    logger.warning(f"Сессия {session_id} уже запущена (PID: {session['pid']})")
                    return False

            # Выбираем скрипт в зависимости от режима
            mode = session['current_mode']
            if mode == 1:
                script_path = self.mode1_script
            elif mode == 2:
                script_path = self.mode2_script
            else:
                logger.error(f"Неизвестный режим: {mode}")
                return False

            if not script_path.exists():
                logger.error(f"Скрипт не найден: {script_path}")
                return False

            # Подготовка аргументов
            args = [
                sys.executable,
                str(script_path),
                str(session['api_id']),
                session['api_hash'],
                session['phone_number'],
                session['session_file'],
                os.getenv('BOT_USERNAME', '@ACarriers_bot'),
                str(session_id)
            ]

            # Для режима 1 добавляем дополнительные параметры
            if mode == 1:
                args.extend([
                    "Появились новые перевозки",  # trigger_message
                    "Список прямых перевозок",     # target_button
                    "0.0"                          # delay
                ])

            logger.info(f"Запуск сессии {session_id} в режиме {mode}")
            logger.debug(f"Команда: {' '.join(args)}")

            # Запуск процесса в фоне
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Ждем немного, чтобы убедиться, что процесс запустился
            time.sleep(2)

            if process.poll() is None:
                # Процесс запущен
                pid = process.pid
                self.db.update_session_status(session_id, 'running', pid)
                logger.info(f"✓ Сессия {session_id} запущена успешно (PID: {pid})")
                return True
            else:
                # Процесс завершился с ошибкой
                stdout, stderr = process.communicate()
                logger.error(f"Не удалось запустить сессию {session_id}")
                logger.error(f"STDOUT: {stdout.decode()}")
                logger.error(f"STDERR: {stderr.decode()}")
                self.db.update_session_status(session_id, 'error')
                return False

        except Exception as e:
            logger.error(f"Ошибка при запуске сессии {session_id}: {e}")
            self.db.update_session_status(session_id, 'error')
            return False

    def stop_session(self, session_id: int, force: bool = False) -> bool:
        """
        Остановить сессию автоматизации

        Args:
            session_id: ID сессии
            force: Принудительная остановка (SIGKILL)

        Returns:
            True если успешно остановлена
        """
        try:
            session = self.db.get_session(session_id)
            if not session:
                logger.error(f"Сессия {session_id} не найдена")
                return False

            pid = session['pid']
            if not pid:
                logger.warning(f"У сессии {session_id} нет PID")
                self.db.update_session_status(session_id, 'stopped')
                return True

            if not self.is_process_running(pid):
                logger.warning(f"Процесс {pid} не запущен")
                self.db.update_session_status(session_id, 'stopped')
                return True

            logger.info(f"Остановка сессии {session_id} (PID: {pid})")

            try:
                process = psutil.Process(pid)

                if force:
                    # Принудительная остановка
                    process.kill()
                    logger.info(f"Процесс {pid} принудительно завершен (SIGKILL)")
                else:
                    # Мягкая остановка
                    process.terminate()
                    logger.info(f"Отправлен сигнал завершения (SIGTERM) процессу {pid}")

                    # Ждем завершения (максимум 10 секунд)
                    try:
                        process.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        logger.warning(f"Процесс {pid} не завершился за 10 секунд, принудительная остановка")
                        process.kill()

                self.db.update_session_status(session_id, 'stopped')
                logger.info(f"✓ Сессия {session_id} остановлена успешно")
                return True

            except psutil.NoSuchProcess:
                logger.warning(f"Процесс {pid} не найден")
                self.db.update_session_status(session_id, 'stopped')
                return True

        except Exception as e:
            logger.error(f"Ошибка при остановке сессии {session_id}: {e}")
            return False

    def restart_session(self, session_id: int) -> bool:
        """
        Перезапустить сессию

        Args:
            session_id: ID сессии

        Returns:
            True если успешно перезапущена
        """
        logger.info(f"Перезапуск сессии {session_id}")

        # Останавливаем
        self.stop_session(session_id)

        # Ждем 2 секунды
        time.sleep(2)

        # Запускаем
        return self.start_session(session_id)

    def switch_mode(self, session_id: int, new_mode: int) -> bool:
        """
        Переключить режим работы сессии

        Args:
            session_id: ID сессии
            new_mode: Новый режим (1 или 2)

        Returns:
            True если успешно переключен
        """
        try:
            session = self.db.get_session(session_id)
            if not session:
                logger.error(f"Сессия {session_id} не найдена")
                return False

            current_mode = session['current_mode']
            if current_mode == new_mode:
                logger.info(f"Сессия {session_id} уже в режиме {new_mode}")
                return True

            logger.info(f"Переключение сессии {session_id} с режима {current_mode} на режим {new_mode}")

            was_running = session['status'] == 'running'

            # Если сессия запущена - останавливаем
            if was_running:
                self.stop_session(session_id)
                time.sleep(1)

            # Обновляем режим в БД
            self.db.update_session_mode(session_id, new_mode)

            # Если была запущена - запускаем снова
            if was_running:
                time.sleep(1)
                success = self.start_session(session_id)
                if success:
                    logger.info(f"✓ Режим сессии {session_id} изменен на {new_mode}")
                    return True
                else:
                    logger.error(f"Не удалось запустить сессию {session_id} после смены режима")
                    return False
            else:
                logger.info(f"✓ Режим сессии {session_id} изменен на {new_mode} (сессия не запущена)")
                return True

        except Exception as e:
            logger.error(f"Ошибка при переключении режима сессии {session_id}: {e}")
            return False

    def is_process_running(self, pid: int) -> bool:
        """
        Проверить, запущен ли процесс

        Args:
            pid: Process ID

        Returns:
            True если процесс запущен
        """
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except:
            return False

    def check_session_status(self, session_id: int) -> Dict[str, Any]:
        """
        Проверить статус сессии

        Args:
            session_id: ID сессии

        Returns:
            Словарь со статусом сессии
        """
        session = self.db.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}

        status = {
            'session_id': session_id,
            'session_name': session['session_name'],
            'mode': session['current_mode'],
            'status': session['status'],
            'pid': session['pid'],
            'is_actually_running': False,
            'uptime': None,
            'stats': {
                'triggers': session['triggers_count'],
                'buttons': session['buttons_clicked'],
                'errors': session['errors_count'],
                'last_trigger': session['last_trigger']
            }
        }

        # Проверяем, действительно ли процесс запущен
        if session['pid']:
            status['is_actually_running'] = self.is_process_running(session['pid'])

            # Если в БД статус running, но процесс не запущен - обновляем
            if session['status'] == 'running' and not status['is_actually_running']:
                self.db.update_session_status(session_id, 'error')
                status['status'] = 'error'

        # Вычисляем uptime
        if session['start_time'] and status['is_actually_running']:
            start_time = datetime.fromisoformat(session['start_time'])
            uptime = datetime.now() - start_time
            status['uptime'] = str(uptime).split('.')[0]

        return status

    def get_session_logs(self, session_id: int, lines: int = 50) -> List[str]:
        """
        Получить последние строки лога сессии

        Args:
            session_id: ID сессии
            lines: Количество строк

        Returns:
            Список строк лога
        """
        try:
            log_dir = Path("logs")
            today = datetime.now().strftime('%Y-%m-%d')
            log_file = log_dir / f"automation_{session_id}_{today}.log"

            if not log_file.exists():
                return [f"Лог-файл не найден: {log_file}"]

            # Читаем последние N строк
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines

        except Exception as e:
            logger.error(f"Ошибка при чтении логов сессии {session_id}: {e}")
            return [f"Ошибка чтения лога: {str(e)}"]

    def parse_log_stats(self, session_id: int) -> Dict[str, Any]:
        """
        Парсинг статистики из логов

        Args:
            session_id: ID сессии

        Returns:
            Словарь со статистикой
        """
        try:
            logs = self.get_session_logs(session_id, lines=1000)

            stats = {
                'triggers': 0,
                'buttons': 0,
                'errors': 0,
                'last_trigger': None,
                'last_action': None
            }

            trigger_pattern = re.compile(r'ТРИГГЕР ОБНАРУЖЕН|ОБНАРУЖЕНЫ НОВЫЕ ПЕРЕВОЗКИ')
            button_pattern = re.compile(r'Кнопка.*успешно нажата')
            error_pattern = re.compile(r'ERROR|Ошибка|❌')
            timestamp_pattern = re.compile(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')

            for line in logs:
                if trigger_pattern.search(line):
                    stats['triggers'] += 1
                    # Извлекаем время
                    match = timestamp_pattern.search(line)
                    if match:
                        stats['last_trigger'] = match.group(1)

                if button_pattern.search(line):
                    stats['buttons'] += 1
                    match = timestamp_pattern.search(line)
                    if match:
                        stats['last_action'] = match.group(1)

                if error_pattern.search(line):
                    stats['errors'] += 1

            # Обновляем статистику в БД
            self.db.update_session_stats(
                session_id,
                triggers=stats['triggers'],
                buttons=stats['buttons'],
                errors=stats['errors']
            )

            return stats

        except Exception as e:
            logger.error(f"Ошибка при парсинге логов сессии {session_id}: {e}")
            return {
                'triggers': 0,
                'buttons': 0,
                'errors': 0,
                'last_trigger': None,
                'last_action': None
            }

    def monitor_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Мониторинг всех сессий

        Returns:
            Список статусов всех сессий
        """
        sessions = self.db.get_all_sessions()
        statuses = []

        for session in sessions:
            status = self.check_session_status(session['id'])
            statuses.append(status)

        return statuses


# Глобальный экземпляр менеджера
_manager_instance = None


def get_session_manager() -> SessionManager:
    """Получить глобальный экземпляр менеджера сессий"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SessionManager()
    return _manager_instance
