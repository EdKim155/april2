"""CRUD operations for database models."""

from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User, Shipment, Booking


# ==================== USER OPERATIONS ====================

async def create_or_update_user(session: AsyncSession, user_id: int, username: Optional[str] = None,
                                 first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
    """Create or update user information."""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Update existing user
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.last_activity = datetime.utcnow()
    else:
        # Create new user
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_all_active_users(session: AsyncSession) -> List[User]:
    """Get all active users."""
    stmt = select(User).where(User.is_active == True)
    result = await session.execute(stmt)
    return result.scalars().all()


# ==================== SHIPMENT OPERATIONS ====================

async def create_shipment(session: AsyncSession, shipment_data: dict) -> Shipment:
    """Create new shipment."""
    shipment = Shipment(**shipment_data)
    session.add(shipment)
    await session.commit()
    await session.refresh(shipment)
    return shipment


async def get_shipment_by_id(session: AsyncSession, shipment_id: str) -> Optional[Shipment]:
    """Get shipment by ID."""
    stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_available_shipments(session: AsyncSession) -> List[Shipment]:
    """Get all available shipments."""
    stmt = select(Shipment).where(Shipment.status == 'available').order_by(Shipment.publication_date.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_user_shipments(session: AsyncSession, username: str) -> List[Shipment]:
    """Get all shipments booked by specific user."""
    stmt = select(Shipment).where(
        and_(
            Shipment.status == 'booked',
            Shipment.booked_by == f'@{username}'
        )
    ).order_by(Shipment.booked_at.desc())
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_all_shipment_ids(session: AsyncSession) -> List[str]:
    """Get all shipment IDs from database."""
    stmt = select(Shipment.shipment_id)
    result = await session.execute(stmt)
    return [row[0] for row in result.all()]


async def book_shipment(session: AsyncSession, shipment_id: str, user_id: int, username: str) -> Tuple[bool, str, Optional[Shipment]]:
    """
    Book a shipment with row-level locking for concurrency control.

    Returns:
        Tuple[bool, str, Optional[Shipment]]: (success, message, shipment)
    """
    # Lock the row for update
    stmt = select(Shipment).where(
        and_(
            Shipment.shipment_id == shipment_id,
            Shipment.status == 'available'
        )
    ).with_for_update()

    result = await session.execute(stmt)
    shipment = result.scalar_one_or_none()

    if not shipment:
        # Shipment already booked, get booking info
        stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
        result = await session.execute(stmt)
        booked_shipment = result.scalar_one_or_none()

        if not booked_shipment:
            return False, "Перевозка не найдена", None

        message = f"Забронировал: {booked_shipment.booked_by}\nВремя бронирования: {booked_shipment.booked_at.strftime('%d.%m.%Y %H:%M')}"
        return False, message, booked_shipment

    # Book the shipment
    shipment.status = 'booked'
    shipment.booked_by = f'@{username}'
    shipment.booked_at = datetime.utcnow()

    # Create booking history record
    booking = Booking(
        shipment_id=shipment_id,
        user_id=user_id,
        username=f'@{username}',
        action='booked'
    )
    session.add(booking)

    await session.commit()
    await session.refresh(shipment)

    return True, "Успешно забронировано", shipment


async def cancel_booking(session: AsyncSession, shipment_id: str, user_id: int, username: str) -> Tuple[bool, str]:
    """
    Cancel a booking.

    Returns:
        Tuple[bool, str]: (success, message)
    """
    stmt = select(Shipment).where(
        and_(
            Shipment.shipment_id == shipment_id,
            Shipment.booked_by == f'@{username}'
        )
    ).with_for_update()

    result = await session.execute(stmt)
    shipment = result.scalar_one_or_none()

    if not shipment:
        return False, "Перевозка не найдена или не забронирована вами"

    # Cancel booking
    shipment.status = 'available'
    shipment.booked_by = None
    shipment.booked_at = None

    # Create cancellation history record
    booking = Booking(
        shipment_id=shipment_id,
        user_id=user_id,
        username=f'@{username}',
        action='cancelled'
    )
    session.add(booking)

    await session.commit()

    return True, f"Перевозка {shipment_id} снова доступна для бронирования"


# ==================== BOOKING HISTORY ====================

async def get_booking_history(session: AsyncSession, user_id: int) -> List[Booking]:
    """Get booking history for user."""
    stmt = select(Booking).where(Booking.user_id == user_id).order_by(Booking.timestamp.desc())
    result = await session.execute(stmt)
    return result.scalars().all()
