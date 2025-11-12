"""Clear all shipments from database."""

import asyncio
from sqlalchemy import select, delete
from bot.database.connection import get_db_session
from bot.database.models import Shipment, Booking


async def main():
    """Clear all shipments and bookings from database."""
    print("🗑️  Clearing all data from database...")

    async with get_db_session() as session:
        # Count before
        result = await session.execute(select(Shipment))
        shipments_count = len(result.scalars().all())

        result = await session.execute(select(Booking))
        bookings_count = len(result.scalars().all())

        print(f"   Found {shipments_count} shipment(s) and {bookings_count} booking(s)")

        # Delete bookings first (foreign key constraint)
        await session.execute(delete(Booking))
        print(f"   Deleted {bookings_count} booking(s)")

        # Delete shipments
        await session.execute(delete(Shipment))
        print(f"   Deleted {shipments_count} shipment(s)")

        await session.commit()

        print("✅ Database is now clean and ready for fresh sync from Google Sheets")


if __name__ == "__main__":
    asyncio.run(main())
