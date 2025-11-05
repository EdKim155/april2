"""Shipment detail and view handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import LOGO_PATH
from bot.database.connection import get_db_session
from bot.database.crud import get_shipment_by_id
from bot.utils.keyboards import build_shipment_detail_keyboard
from bot.utils.messages import get_shipment_detail_message

logger = logging.getLogger(__name__)


async def _edit_message_with_keyboard(query, message: str, keyboard):
    """Helper to edit message caption and keyboard."""
    try:
        await query.edit_message_caption(
            caption=message,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        chat = query.message.chat
        await query.message.delete()
        with open(LOGO_PATH, 'rb') as photo:
            await chat.send_photo(
                photo=photo,
                caption=message,
                reply_markup=keyboard
            )


async def handle_view_shipment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle viewing shipment details.

    Callback data format: shipment:view:prefix:shipment_id:page
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    callback_data = query.data.split(':')
    prefix = callback_data[2]  # 'direct' or 'my'
    shipment_id = callback_data[3]
    page = int(callback_data[4])

    user = update.effective_user
    username = user.username or user.first_name

    # Get shipment details from database
    async with get_db_session() as session:
        shipment = await get_shipment_by_id(session, shipment_id)

    if not shipment:
        await query.answer("❌ Перевозка не найдена", show_alert=True)
        return

    # Check if booked by current user
    is_booked_by_user = (
        shipment.status == 'booked' and
        shipment.booked_by == f'@{username}'
    )

    # Build message and keyboard
    message = get_shipment_detail_message(shipment)
    keyboard = build_shipment_detail_keyboard(
        shipment=shipment,
        is_booked_by_user=is_booked_by_user,
        page=page,
        prefix=prefix
    )

    await _edit_message_with_keyboard(query, message, keyboard)
