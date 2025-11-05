"""Main bot application entry point."""

import asyncio
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import BOT_TOKEN, TIMEZONE, PUBLISH_HOUR, PUBLISH_MINUTE
from bot.database.connection import init_db
from bot.google_sheets.manager import GoogleSheetManager
from bot.handlers.start import start_command
from bot.handlers.callbacks import callback_query_handler
from bot.scheduler.background import BackgroundSyncTask
from bot.scheduler.jobs import daily_publication_job

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)


class AprilBot:
    """Main bot application class."""

    def __init__(self):
        """Initialize bot application."""
        self.application = None
        self.sheet_manager = None
        self.background_sync = None
        self.scheduler = None

    async def post_init(self, application: Application) -> None:
        """
        Post initialization callback.

        Args:
            application: Telegram application instance
        """
        logger.info("🔧 Initializing bot components...")

        # Initialize database
        try:
            await init_db()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

        # Initialize Google Sheets manager
        try:
            self.sheet_manager = GoogleSheetManager()
            application.bot_data['sheet_manager'] = self.sheet_manager
            logger.info("✅ Google Sheets manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets manager: {e}")
            logger.warning("⚠️ Bot will continue without Google Sheets integration")
            self.sheet_manager = None

        # Start background sync task
        if self.sheet_manager:
            self.background_sync = BackgroundSyncTask(application.bot, self.sheet_manager)
            await self.background_sync.start()
            logger.info("✅ Background sync task started")

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)

        # Add daily publication job
        self.scheduler.add_job(
            daily_publication_job,
            'cron',
            hour=PUBLISH_HOUR,
            minute=PUBLISH_MINUTE,
            args=[application.bot],
            id='daily_publication',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"✅ Scheduler started (daily publication at {PUBLISH_HOUR}:{PUBLISH_MINUTE:02d})")

    async def post_shutdown(self, application: Application) -> None:
        """
        Post shutdown callback.

        Args:
            application: Telegram application instance
        """
        logger.info("🛑 Shutting down bot components...")

        # Stop background sync
        if self.background_sync:
            await self.background_sync.stop()
            logger.info("✅ Background sync stopped")

        # Stop scheduler
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Scheduler stopped")

    def build_application(self) -> Application:
        """
        Build and configure the Telegram application.

        Returns:
            Application: Configured Telegram application
        """
        # Create application
        application = (
            Application.builder()
            .token(BOT_TOKEN)
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .build()
        )

        # Add command handlers
        application.add_handler(CommandHandler("start", start_command))

        # Add callback query handler
        application.add_handler(CallbackQueryHandler(callback_query_handler))

        logger.info("✅ Application handlers registered")

        return application

    def run(self):
        """Run the bot."""
        logger.info("🤖 Starting April Shipments Bot v2.0...")

        if not BOT_TOKEN:
            logger.error("❌ BOT_TOKEN is not set in environment variables")
            sys.exit(1)

        # Build application
        self.application = self.build_application()

        # Run bot
        logger.info("🚀 Bot is running...")
        self.application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )


def main():
    """Main entry point."""
    try:
        bot = AprilBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
