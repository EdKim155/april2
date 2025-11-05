"""Check database content."""

import asyncio
from sqlalchemy import select
from bot.database.connection import get_db_session
from bot.database.models import Shipment


async def main():
    """Check what's in the database."""
    print("🔍 Checking database content...\n")

    async with get_db_session() as session:
        # Get all shipments
        result = await session.execute(select(Shipment))
        shipments = result.scalars().all()

        if not shipments:
            print("❌ No shipments found in database")
            return

        print(f"✅ Found {len(shipments)} shipment(s) in database:\n")

        for i, shipment in enumerate(shipments, 1):
            print(f"{i}. ID: {shipment.shipment_id}")
            print(f"   Direction: {shipment.direction}")
            print(f"   Status: {shipment.status}")
            print(f"   Loading: {shipment.loading_point}")
            print(f"   Date: {shipment.loading_date}")
            print(f"   Weight: {shipment.weight}")
            print(f"   Volume: {shipment.volume}")
            print(f"   Cost: {shipment.cost}")
            print(f"   Vehicle: {shipment.vehicle}")
            print(f"   Driver: {shipment.driver}")
            if shipment.booked_by:
                print(f"   Booked by: {shipment.booked_by}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
