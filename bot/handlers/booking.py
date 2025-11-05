"""Booking and cancellation handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.database.connection import get_db_session
from bot.database.crud import book_shipment, cancel_booking
from bot.utils.keyboards import (
    build_booking_success_keyboard,
    build_booking_failed_keyboard,
    build_cancellation_success_keyboard
)
from bot.utils.messages import (
    get_booking_success_message,
    get_booking_failed_message,
    get_cancellation_success_message
)

logger = logging.getLogger(__name__)


async def handle_book_shipment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle shipment booking.

    Callback data format: shipment:book:shipment_id:page:prefix
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    callback_data = query.data.split(':')
    shipment_id = callback_data[2]
    page = int(callback_data[3]) if len(callback_data) > 3 else 0
    prefix = callback_data[4] if len(callback_data) > 4 else "direct"

    user = update.effective_user
    username = user.username or user.first_name

    logger.info(f"📦 User {user.id} (@{username}) attempting to book shipment {shipment_id}")

    # Try to book shipment with database lock
    async with get_db_session() as session:
        success, message_text, shipment = await book_shipment(
            session=session,
            shipment_id=shipment_id,
            user_id=user.id,
            username=username
        )

    if success:
        # Booking successful
        logger.info(f"✅ Shipment {shipment_id} booked by @{username}")

        # Update Google Sheet
        if context.bot_data.get('sheet_manager'):
            try:
                sheet_manager = context.bot_data['sheet_manager']
                await context.application.bot.loop.run_in_executor(
                    None,
                    sheet_manager.update_booking_status,
                    shipment_id,
                    username
                )
            except Exception as e:
                logger.error(f"❌ Failed to update Google Sheet: {e}")

        message = get_booking_success_message(shipment_id, shipment.direction)
        keyboard = build_booking_success_keyboard()
    else:
        # Booking failed (already booked)
        logger.warning(f"❌ Shipment {shipment_id} already booked: {message_text}")

        if shipment:
            booked_at = shipment.booked_at.strftime('%d.%m.%Y %H:%M')
            message = get_booking_failed_message(shipment_id, shipment.booked_by, booked_at)
        else:
            message = f"❌ Перевозка {shipment_id} уже забронирована"

        keyboard = build_booking_failed_keyboard()

    await query.edit_message_text(
        text=message,
        reply_markup=keyboard
    )


async def handle_cancel_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle booking cancellation.

    Callback data format: shipment:cancel:shipment_id:page
    """
    query = update.callback_query
    await query.answer()

    # Parse callback data
    callback_data = query.data.split(':')
    shipment_id = callback_data[2]
    page = int(callback_data[3]) if len(callback_data) > 3 else 0

    user = update.effective_user
    username = user.username or user.first_name

    logger.info(f"🔄 User {user.id} (@{username}) attempting to cancel booking {shipment_id}")

    # Try to cancel booking
    async with get_db_session() as session:
        success, message_text = await cancel_booking(
            session=session,
            shipment_id=shipment_id,
            user_id=user.id,
            username=username
        )

    if success:
        # Cancellation successful
        logger.info(f"✅ Booking cancelled for shipment {shipment_id} by @{username}")

        # Update Google Sheet
        if context.bot_data.get('sheet_manager'):
            try:
                sheet_manager = context.bot_data['sheet_manager']
                await context.application.bot.loop.run_in_executor(
                    None,
                    sheet_manager.cancel_booking,
                    shipment_id
                )
            except Exception as e:
                logger.error(f"❌ Failed to update Google Sheet: {e}")

        message = get_cancellation_success_message(shipment_id)
        keyboard = build_cancellation_success_keyboard()
    else:
        # Cancellation failed
        logger.warning(f"❌ Failed to cancel booking {shipment_id}: {message_text}")
        message = f"❌ {message_text}"
        keyboard = build_cancellation_success_keyboard()

    await query.edit_message_text(
        text=message,
        reply_markup=keyboard
    )
