"""Start command handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.database.connection import get_db_session
from bot.database.crud import create_or_update_user
from bot.utils.keyboards import build_main_menu_keyboard
from bot.utils.messages import get_welcome_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.

    Shows welcome message with main menu.
    """
    user = update.effective_user

    # Create or update user in database
    async with get_db_session() as session:
        await create_or_update_user(
            session=session,
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )

    logger.info(f"👤 User {user.id} (@{user.username}) started the bot")

    # Send welcome message with main menu
    keyboard = build_main_menu_keyboard()
    message = get_welcome_message()

    await update.message.reply_text(
        text=message,
        reply_markup=keyboard
    )
