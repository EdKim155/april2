"""Background tasks for continuous operations."""

import asyncio
import logging
from telegram import Bot

from bot.config import SYNC_INTERVAL
from bot.database.connection import get_db_session
from bot.database.crud import get_all_active_users
from bot.google_sheets.manager import GoogleSheetManager
from bot.google_sheets.sync import sync_from_google_sheet, sync_statuses_from_google_sheet, sync_deletions_from_google_sheet
from bot.utils.notifications import notify_users_about_new_shipments

logger = logging.getLogger(__name__)


class BackgroundSyncTask:
    """Background task for syncing with Google Sheets every 10 seconds."""

    def __init__(self, bot: Bot, sheet_manager: GoogleSheetManager):
        """
        Initialize background sync task.

        Args:
            bot: Telegram Bot instance
            sheet_manager: Google Sheets manager instance
        """
        self.bot = bot
        self.sheet_manager = sheet_manager
        self.is_running = False
        self.task = None

    async def start(self):
        """Start the background sync task."""
        if self.is_running:
            logger.warning("⚠️ Background sync task is already running")
            return

        self.is_running = True
        self.task = asyncio.create_task(self._run())
        logger.info("🚀 Background sync task started")

    async def stop(self):
        """Stop the background sync task."""
        if not self.is_running:
            return

        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 Background sync task stopped")

    async def _run(self):
        """Run the background sync loop."""
        logger.info(f"🔄 Starting background sync with interval: {SYNC_INTERVAL} seconds")

        while self.is_running:
            try:
                await self._sync_iteration()
            except Exception as e:
                logger.error(f"❌ Error in sync iteration: {e}", exc_info=True)

            # Wait for next iteration
            await asyncio.sleep(SYNC_INTERVAL)

    async def _sync_iteration(self):
        """Perform one sync iteration."""
        try:
            async with get_db_session() as session:
                # 1. Удаление перевозок, которых нет в таблице
                deleted_count = await sync_deletions_from_google_sheet(session, self.sheet_manager)
                if deleted_count > 0:
                    logger.info(f"🗑️  Удалено перевозок из БД: {deleted_count}")
                
                # 2. Синхронизация статусов существующих перевозок из таблицы в БД
                updated_count = await sync_statuses_from_google_sheet(session, self.sheet_manager)
                if updated_count > 0:
                    logger.info(f"🔄 Обновлено статусов из таблицы: {updated_count}")
                
                # 3. Синхронизация НОВЫХ перевозок из таблицы
                new_shipment_ids = await sync_from_google_sheet(session, self.sheet_manager)

                if new_shipment_ids:
                    logger.info(f"🆕 Найдено новых перевозок: {len(new_shipment_ids)}")

                    # Получаем всех активных пользователей
                    users = await get_all_active_users(session)

                    # Отправляем уведомления пользователям
                    if users:
                        notified_count = await notify_users_about_new_shipments(self.bot, users)
                        logger.info(f"📢 Отправлено уведомлений: {notified_count}/{len(users)}")

        except Exception as e:
            logger.error(f"❌ Ошибка синхронизации: {e}", exc_info=True)
