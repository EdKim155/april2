"""Menu navigation handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import LOGO_PATH
from bot.database.connection import get_db_session
from bot.database.crud import get_available_shipments, get_user_shipments
from bot.utils.keyboards import (
    build_main_menu_keyboard,
    build_shipments_list_keyboard,
    build_stub_keyboard
)
from bot.utils.messages import (
    get_welcome_message,
    get_no_shipments_message,
    get_stub_message,
    get_no_my_shipments_message,
    get_my_shipments_header
)

logger = logging.getLogger(__name__)


async def _send_photo_with_keyboard(query, message: str, keyboard):
    """Helper to send photo with message and keyboard."""
    await query.message.delete()
    with open(LOGO_PATH, 'rb') as photo:
        await query.message.reply_photo(
            photo=photo,
            caption=message,
            reply_markup=keyboard
        )


async def handle_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back to main menu navigation."""
    query = update.callback_query
    await query.answer()

    keyboard = build_main_menu_keyboard()
    message = get_welcome_message()

    await _send_photo_with_keyboard(query, message, keyboard)


async def handle_direct_shipments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct shipments list menu."""
    query = update.callback_query
    await query.answer()

    # Extract page number if provided
    callback_data = query.data.split(':')
    page = int(callback_data[2]) if len(callback_data) > 2 else 0

    # Get available shipments from database
    async with get_db_session() as session:
        shipments = await get_available_shipments(session)

    if not shipments:
        # No shipments available
        keyboard = build_shipments_list_keyboard([], page=0, prefix="direct")
        message = get_no_shipments_message()
    else:
        # Build shipments list
        keyboard = build_shipments_list_keyboard(shipments, page=page, prefix="direct")
        message = get_welcome_message()

    await _send_photo_with_keyboard(query, message, keyboard)


async def handle_my_shipments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle my shipments menu."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    username = user.username or user.first_name

    # Extract page number if provided
    callback_data = query.data.split(':')
    page = int(callback_data[2]) if len(callback_data) > 2 else 0

    # Get user's booked shipments
    async with get_db_session() as session:
        shipments = await get_user_shipments(session, username)

    if not shipments:
        # User has no booked shipments
        keyboard = build_shipments_list_keyboard([], page=0, prefix="my")
        message = get_no_my_shipments_message()
    else:
        # Build user's shipments list
        keyboard = build_shipments_list_keyboard(shipments, page=page, prefix="my")
        message = get_my_shipments_header()

    await _send_photo_with_keyboard(query, message, keyboard)


async def handle_highway_shipments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle highway shipments menu (stub)."""
    query = update.callback_query
    await query.answer()

    keyboard = build_stub_keyboard()
    message = get_stub_message()

    await _send_photo_with_keyboard(query, message, keyboard)


async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle settings menu (stub)."""
    query = update.callback_query
    await query.answer()

    keyboard = build_stub_keyboard()
    message = get_stub_message()

    await _send_photo_with_keyboard(query, message, keyboard)


async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination for shipment lists."""
    query = update.callback_query
    await query.answer()

    # Parse callback data: page:prefix:page_number
    callback_data = query.data.split(':')
    prefix = callback_data[1]  # 'direct' or 'my'
    page = int(callback_data[2])

    if prefix == "direct":
        # Get available shipments
        async with get_db_session() as session:
            shipments = await get_available_shipments(session)
        message = get_welcome_message()
    elif prefix == "my":
        # Get user's booked shipments
        user = update.effective_user
        username = user.username or user.first_name
        async with get_db_session() as session:
            shipments = await get_user_shipments(session, username)
        message = get_my_shipments_header()
    else:
        return

    keyboard = build_shipments_list_keyboard(shipments, page=page, prefix=prefix)

    await _send_photo_with_keyboard(query, message, keyboard)
