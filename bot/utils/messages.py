"""Message templates for bot responses."""

from bot.database.models import Shipment


# Brand logo (text-based)
LOGO = """
╔══════════════════════════════╗
║   АПРЕЛЬ сеть аптек          ║
╚══════════════════════════════╝
"""


def get_welcome_message() -> str:
    """Get welcome message for /start command."""
    return f"""{LOGO}

Пришлем сообщение как только будут назначены перевозки"""


def get_new_shipments_notification() -> str:
    """Get notification message for new shipments."""
    return """Появились новые перевозки.
Нажмите /start для вызова меню"""


def get_no_shipments_message() -> str:
    """Get message when no shipments available."""
    return f"""{LOGO}

Перевозок нет"""


def get_no_my_shipments_message() -> str:
    """Get message when user has no booked shipments."""
    return f"""{LOGO}

📋 Мои перевозки:

У вас пока нет забронированных перевозок"""


def get_my_shipments_header() -> str:
    """Get header for my shipments list."""
    return f"""{LOGO}

📋 Мои перевозки:"""


def get_shipment_detail_message(shipment: Shipment) -> str:
    """
    Get detailed shipment information message.

    Args:
        shipment: Shipment object

    Returns:
        str: Formatted shipment detail message
    """
    loading_date = shipment.loading_date.strftime('%Y-%m-%d %H:%M:%S')

    message = f"""{LOGO}

Погрузка: {shipment.loading_point}
Номер: {shipment.shipment_id}
Дата и время подачи авто: будет готова к погрузке до {loading_date}
Направление: {shipment.direction}
Вес: {shipment.weight}
Объём: {shipment.volume}
Начальная точка: {shipment.start_address}
Конечная точка: {shipment.end_address}
Количество точек: {shipment.points_count}
Расстояние: {shipment.distance} км.
Стоимость (Без НДС): {shipment.cost}
Автомобиль: {shipment.vehicle}
Водитель: {shipment.driver}"""

    return message


def get_booking_success_message(shipment_id: str, direction: str) -> str:
    """
    Get successful booking message.

    Args:
        shipment_id: Shipment ID
        direction: Direction name

    Returns:
        str: Formatted success message
    """
    return f"""{LOGO}

✅ Перевозка {shipment_id} успешно забронирована!

Направление: {direction}
Ваше имя добавлено в систему."""


def get_booking_failed_message(shipment_id: str, booked_by: str, booked_at: str) -> str:
    """
    Get failed booking message (already booked).

    Args:
        shipment_id: Shipment ID
        booked_by: Username who booked
        booked_at: Booking timestamp

    Returns:
        str: Formatted failure message
    """
    return f"""{LOGO}

❌ Перевозка {shipment_id} уже забронирована

Забронировал: {booked_by}
Время бронирования: {booked_at}"""


def get_cancellation_success_message(shipment_id: str) -> str:
    """
    Get successful cancellation message.

    Args:
        shipment_id: Shipment ID

    Returns:
        str: Formatted cancellation message
    """
    return f"""{LOGO}

✅ Бронирование отменено

Перевозка {shipment_id} снова доступна для бронирования."""


def get_stub_message() -> str:
    """Get stub message for features under development."""
    return f"""{LOGO}

Раздел находится в разработке"""
