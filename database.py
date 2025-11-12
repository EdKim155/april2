#!/usr/bin/env python3
"""
База данных для управления автоматизацией April Shipments
Управление пользователями, сессиями и логами доступа
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class Database:
    """Класс для работы с базой данных SQLite"""

    def __init__(self, db_path: str = "control_bot.db"):
        """
        Инициализация базы данных

        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.connection = None
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Получение подключения к БД"""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
        return self.connection

    def _initialize_database(self):
        """Создание таблиц базы данных"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_access TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Таблица сессий автоматизации
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                session_file TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                current_mode INTEGER DEFAULT 1,
                status TEXT DEFAULT 'stopped',
                pid INTEGER DEFAULT NULL,
                start_time TIMESTAMP DEFAULT NULL,
                last_trigger TIMESTAMP DEFAULT NULL,
                triggers_count INTEGER DEFAULT 0,
                buttons_clicked INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица логов доступа
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                action TEXT,
                session_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        conn.commit()
        logger.info("База данных инициализирована")

    # ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

    def add_user(self, user_id: int, username: str = None, first_name: str = None) -> bool:
        """
        Добавить пользователя в базу

        Args:
            user_id: Telegram User ID
            username: Telegram username
            first_name: Имя пользователя

        Returns:
            True если успешно добавлен
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, username, first_name, date_added, is_active)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
            """, (user_id, username, first_name))
            conn.commit()
            logger.info(f"Пользователь {user_id} ({username}) добавлен в базу")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении пользователя: {e}")
            return False

    def remove_user(self, user_id: int) -> bool:
        """
        Удалить пользователя из базы (деактивировать)

        Args:
            user_id: Telegram User ID

        Returns:
            True если успешно удален
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Пользователь {user_id} деактивирован")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении пользователя: {e}")
            return False

    def is_user_authorized(self, user_id: int) -> bool:
        """
        Проверка авторизации пользователя

        Args:
            user_id: Telegram User ID

        Returns:
            True если пользователь авторизован
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT is_active FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result is not None and result['is_active'] == 1
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}")
            return False

    def update_last_access(self, user_id: int):
        """
        Обновить время последнего доступа пользователя

        Args:
            user_id: Telegram User ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET last_access = CURRENT_TIMESTAMP WHERE user_id = ?
            """, (user_id,))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени доступа: {e}")

    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Получить список всех пользователей

        Returns:
            Список пользователей
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY date_added DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении списка пользователей: {e}")
            return []

    # ==================== УПРАВЛЕНИЕ СЕССИЯМИ ====================

    def add_session(self, session_name: str, phone_number: str, api_id: int,
                   api_hash: str, session_file: str) -> Optional[int]:
        """
        Добавить новую сессию

        Args:
            session_name: Название сессии
            phone_number: Номер телефона
            api_id: Telegram API ID
            api_hash: Telegram API Hash
            session_file: Путь к файлу сессии

        Returns:
            ID созданной сессии или None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_name, phone_number, api_id, api_hash, session_file)
                VALUES (?, ?, ?, ?, ?)
            """, (session_name, phone_number, api_id, api_hash, session_file))
            conn.commit()
            session_id = cursor.lastrowid
            logger.info(f"Сессия {session_name} добавлена с ID {session_id}")
            return session_id
        except Exception as e:
            logger.error(f"Ошибка при добавлении сессии: {e}")
            return None

    def get_session(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о сессии

        Args:
            session_id: ID сессии

        Returns:
            Словарь с данными сессии или None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка при получении сессии: {e}")
            return None

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Получить список всех сессий

        Returns:
            Список сессий
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions ORDER BY id")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении списка сессий: {e}")
            return []

    def update_session_status(self, session_id: int, status: str, pid: Optional[int] = None):
        """
        Обновить статус сессии

        Args:
            session_id: ID сессии
            status: Новый статус (running, stopped, error)
            pid: Process ID (опционально)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if status == "running":
                cursor.execute("""
                    UPDATE sessions
                    SET status = ?, pid = ?, start_time = CURRENT_TIMESTAMP, is_active = 1
                    WHERE id = ?
                """, (status, pid, session_id))
            elif status == "stopped":
                cursor.execute("""
                    UPDATE sessions
                    SET status = ?, pid = NULL, is_active = 0
                    WHERE id = ?
                """, (status, session_id))
            else:  # error
                cursor.execute("""
                    UPDATE sessions
                    SET status = ?, pid = NULL, is_active = 0
                    WHERE id = ?
                """, (status, session_id))

            conn.commit()
            logger.info(f"Статус сессии {session_id} обновлен на {status}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении статуса сессии: {e}")

    def update_session_mode(self, session_id: int, mode: int):
        """
        Изменить режим работы сессии

        Args:
            session_id: ID сессии
            mode: Режим работы (1 или 2)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET current_mode = ? WHERE id = ?", (mode, session_id))
            conn.commit()
            logger.info(f"Режим сессии {session_id} изменен на {mode}")
        except Exception as e:
            logger.error(f"Ошибка при изменении режима сессии: {e}")

    def update_session_stats(self, session_id: int, triggers: int = None,
                            buttons: int = None, errors: int = None):
        """
        Обновить статистику сессии

        Args:
            session_id: ID сессии
            triggers: Количество триггеров (опционально)
            buttons: Количество нажатых кнопок (опционально)
            errors: Количество ошибок (опционально)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            updates = []
            params = []

            if triggers is not None:
                updates.append("triggers_count = ?")
                params.append(triggers)
                updates.append("last_trigger = CURRENT_TIMESTAMP")

            if buttons is not None:
                updates.append("buttons_clicked = ?")
                params.append(buttons)

            if errors is not None:
                updates.append("errors_count = ?")
                params.append(errors)

            if updates:
                params.append(session_id)
                query = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении статистики сессии: {e}")

    def delete_session(self, session_id: int) -> bool:
        """
        Удалить сессию из базы

        Args:
            session_id: ID сессии

        Returns:
            True если успешно удалена
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()
            logger.info(f"Сессия {session_id} удалена")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении сессии: {e}")
            return False

    # ==================== ЛОГИРОВАНИЕ ДЕЙСТВИЙ ====================

    def log_access(self, user_id: int, username: str, action: str,
                   session_id: Optional[int] = None, details: str = None):
        """
        Залогировать действие пользователя

        Args:
            user_id: Telegram User ID
            username: Telegram username
            action: Действие
            session_id: ID сессии (опционально)
            details: Дополнительные детали (опционально)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO access_logs (user_id, username, action, session_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, action, session_id, details))
            conn.commit()
        except Exception as e:
            logger.error(f"Ошибка при логировании действия: {e}")

    def get_access_logs(self, user_id: Optional[int] = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получить логи доступа

        Args:
            user_id: Фильтр по пользователю (опционально)
            limit: Максимальное количество записей

        Returns:
            Список логов
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            if user_id:
                cursor.execute("""
                    SELECT * FROM access_logs
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM access_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении логов: {e}")
            return []

    def close(self):
        """Закрыть подключение к базе данных"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Подключение к БД закрыто")


# Глобальный экземпляр базы данных
_db_instance = None


def get_database() -> Database:
    """Получить глобальный экземпляр базы данных"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
