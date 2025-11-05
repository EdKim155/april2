"""Callback query router for handling all inline button callbacks."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.menu import (
    handle_back_to_menu,
    handle_direct_shipments,
    handle_my_shipments,
    handle_highway_shipments,
    handle_settings,
    handle_pagination
)
from bot.handlers.shipments import handle_view_shipment
from bot.handlers.booking import handle_book_shipment, handle_cancel_booking

logger = logging.getLogger(__name__)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main callback query router.

    Routes callback queries to appropriate handlers based on callback_data prefix.
    """
    query = update.callback_query

    if not query or not query.data:
        return

    callback_data = query.data

    try:
        # Route to appropriate handler
        if callback_data == "noop":
            # No operation (pagination counter)
            await query.answer()

        elif callback_data.startswith("nav:back_to_menu"):
            await handle_back_to_menu(update, context)

        elif callback_data.startswith("menu:direct_shipments"):
            await handle_direct_shipments(update, context)

        elif callback_data.startswith("menu:my_shipments"):
            await handle_my_shipments(update, context)

        elif callback_data.startswith("menu:highway_shipments"):
            await handle_highway_shipments(update, context)

        elif callback_data.startswith("menu:settings"):
            await handle_settings(update, context)

        elif callback_data.startswith("page:"):
            await handle_pagination(update, context)

        elif callback_data.startswith("shipment:view:"):
            await handle_view_shipment(update, context)

        elif callback_data.startswith("shipment:book:"):
            await handle_book_shipment(update, context)

        elif callback_data.startswith("shipment:cancel:"):
            await handle_cancel_booking(update, context)

        else:
            logger.warning(f"⚠️ Unknown callback data: {callback_data}")
            await query.answer("Неизвестная команда", show_alert=True)

    except Exception as e:
        logger.error(f"❌ Error handling callback {callback_data}: {e}", exc_info=True)
        await query.answer("Произошла ошибка. Попробуйте снова.", show_alert=True)
