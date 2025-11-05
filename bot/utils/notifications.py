"""Notification utilities for sending messages to users."""

import logging
from typing import List
from telegram import Bot
from telegram.error import TelegramError

from bot.database.models import User
from bot.utils.messages import get_new_shipments_notification

logger = logging.getLogger(__name__)


async def notify_users_about_new_shipments(bot: Bot, users: List[User]) -> int:
    """
    Notify all active users about new shipments.

    Args:
        bot: Telegram Bot instance
        users: List of users to notify

    Returns:
        int: Number of successfully notified users
    """
    message = get_new_shipments_notification()
    success_count = 0

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.user_id,
                text=message
            )
            success_count += 1
        except TelegramError as e:
            logger.error(f"❌ Failed to send notification to user {user.user_id}: {e}")
            continue

    logger.info(f"📤 Sent notifications to {success_count}/{len(users)} users")
    return success_count
