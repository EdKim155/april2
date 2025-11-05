"""Scheduled jobs for periodic tasks."""

import logging
from telegram import Bot

from bot.config import PUBLISH_HOUR, PUBLISH_MINUTE, TIMEZONE
from bot.database.connection import get_db_session
from bot.database.crud import get_all_active_users, get_available_shipments
from bot.utils.notifications import notify_users_about_new_shipments

logger = logging.getLogger(__name__)


async def daily_publication_job(bot: Bot):
    """
    Daily publication job that runs at 11:30 MSK.

    This job checks if there are available shipments and notifies users.
    """
    logger.info(f"⏰ Daily publication job triggered at {PUBLISH_HOUR}:{PUBLISH_MINUTE:02d}")

    try:
        async with get_db_session() as session:
            # Check if there are available shipments
            shipments = await get_available_shipments(session)

            if shipments:
                logger.info(f"📦 Found {len(shipments)} available shipments for daily publication")

                # Get all active users
                users = await get_all_active_users(session)

                if users:
                    # Notify users about available shipments
                    notified_count = await notify_users_about_new_shipments(bot, users)
                    logger.info(f"📢 Daily publication: notified {notified_count} users")
                else:
                    logger.warning("⚠️ No active users to notify")
            else:
                logger.info("ℹ️ No available shipments for daily publication")

    except Exception as e:
        logger.error(f"❌ Daily publication job failed: {e}", exc_info=True)
