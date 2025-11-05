"""Keyboard builders for bot inline keyboards."""

from typing import List
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.database.models import Shipment
from bot.config import SHIPMENTS_PER_PAGE


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build main menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔔 Список прямых перевозок", callback_data="menu:direct_shipments")],
        [InlineKeyboardButton("📋 Список магистральных перевозок", callback_data="menu:highway_shipments")],
        [InlineKeyboardButton("📋 Мои перевозки", callback_data="menu:my_shipments")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="menu:settings")]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_shipments_list_keyboard(shipments: List[Shipment], page: int = 0, prefix: str = "direct") -> InlineKeyboardMarkup:
    """
    Build shipments list keyboard with pagination.

    Args:
        shipments: List of shipments
        page: Current page number (0-indexed)
        prefix: Prefix for callback data (direct/my)

    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []

    if not shipments:
        # No shipments available
        keyboard.append([InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")])
        return InlineKeyboardMarkup(keyboard)

    # Calculate pagination
    total_pages = (len(shipments) - 1) // SHIPMENTS_PER_PAGE + 1
    start_idx = page * SHIPMENTS_PER_PAGE
    end_idx = min(start_idx + SHIPMENTS_PER_PAGE, len(shipments))

    # Add shipment buttons
    for shipment in shipments[start_idx:end_idx]:
        button_text = f"🚛 {shipment.shipment_id} {shipment.direction}"
        callback_data = f"shipment:view:{prefix}:{shipment.shipment_id}:{page}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    # Add pagination buttons if needed
    if total_pages > 1:
        pagination_row = []
        if page > 0:
            pagination_row.append(InlineKeyboardButton("◀️", callback_data=f"page:{prefix}:{page-1}"))
        pagination_row.append(InlineKeyboardButton(f"{page + 1} из {total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            pagination_row.append(InlineKeyboardButton("▶️", callback_data=f"page:{prefix}:{page+1}"))
        keyboard.append(pagination_row)

    # Add back button
    keyboard.append([InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")])

    return InlineKeyboardMarkup(keyboard)


def build_shipment_detail_keyboard(shipment: Shipment, is_booked_by_user: bool = False, page: int = 0, prefix: str = "direct") -> InlineKeyboardMarkup:
    """
    Build shipment detail keyboard.

    Args:
        shipment: Shipment object
        is_booked_by_user: Whether shipment is booked by current user
        page: Current page number for back navigation
        prefix: Prefix for callback data (direct/my)

    Returns:
        InlineKeyboardMarkup
    """
    keyboard = []

    if shipment.status == 'available':
        # Show book button if available
        keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data=f"shipment:book:{shipment.shipment_id}:{page}:{prefix}")])
    elif is_booked_by_user:
        # Show cancel button if booked by current user
        keyboard.append([InlineKeyboardButton("❌ Отменить бронирование", callback_data=f"shipment:cancel:{shipment.shipment_id}:{page}")])

    # Back button
    if prefix == "my":
        keyboard.append([InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 К списку", callback_data=f"menu:direct_shipments:{page}")])
        keyboard.append([InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")])

    return InlineKeyboardMarkup(keyboard)


def build_booking_success_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for successful booking."""
    keyboard = [
        [InlineKeyboardButton("📋 Мои перевозки", callback_data="menu:my_shipments")],
        [InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_booking_failed_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for failed booking (already booked)."""
    keyboard = [
        [InlineKeyboardButton("🔔 Список прямых перевозок", callback_data="menu:direct_shipments")],
        [InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_cancellation_success_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for successful cancellation."""
    keyboard = [
        [InlineKeyboardButton("🔔 Список прямых перевозок", callback_data="menu:direct_shipments")],
        [InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def build_stub_keyboard() -> InlineKeyboardMarkup:
    """Build keyboard for stub pages (under development)."""
    keyboard = [
        [InlineKeyboardButton("🔄 Возврат в меню", callback_data="nav:back_to_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
