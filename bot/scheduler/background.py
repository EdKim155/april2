"""Background tasks for continuous operations."""

import asyncio
import logging
from telegram import Bot

from bot.config import SYNC_INTERVAL
from bot.database.connection import get_db_session
from bot.database.crud import get_all_active_users
from bot.google_sheets.manager import GoogleSheetManager
from bot.google_sheets.sync import sync_from_google_sheet
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
            # Sync from Google Sheet
            async with get_db_session() as session:
                new_shipment_ids = await sync_from_google_sheet(session, self.sheet_manager)

                if new_shipment_ids:
                    logger.info(f"🆕 Found {len(new_shipment_ids)} new shipments: {new_shipment_ids}")

                    # Get all active users
                    users = await get_all_active_users(session)

                    # Notify users about new shipments
                    if users:
                        notified_count = await notify_users_about_new_shipments(self.bot, users)
                        logger.info(f"📢 Notified {notified_count} users about new shipments")

        except Exception as e:
            logger.error(f"❌ Sync iteration failed: {e}", exc_info=True)
