"""Export shipments from database to Google Sheets."""

import asyncio
from sqlalchemy import select
from bot.database.connection import get_db_session
from bot.database.models import Shipment
from bot.google_sheets.manager import GoogleSheetManager


async def export_shipments():
    """Export all shipments from DB to Google Sheets."""
    print("🔄 Starting export from Database to Google Sheets...\n")

    # Initialize Google Sheets
    sheet_manager = GoogleSheetManager()

    # Get all shipments from database
    async with get_db_session() as session:
        result = await session.execute(select(Shipment).order_by(Shipment.shipment_id))
        shipments = result.scalars().all()

        if not shipments:
            print("❌ No shipments found in database")
            return

        print(f"✅ Found {len(shipments)} shipment(s) in database\n")

        # Prepare data for Google Sheets
        rows_to_add = []

        for shipment in shipments:
            # Format date as string
            loading_date_str = shipment.loading_date.strftime('%Y-%m-%d %H:%M:%S')
            booked_at_str = shipment.booked_at.strftime('%Y-%m-%d %H:%M:%S') if shipment.booked_at else ''

            # Create row matching the column order
            row = [
                str(shipment.shipment_id),          # A: shipment_id
                str(shipment.loading_point),        # B: loading_point
                loading_date_str,                   # C: loading_date
                str(shipment.direction),            # D: direction
                str(shipment.weight),               # E: weight
                str(shipment.volume),               # F: volume
                str(shipment.start_address),        # G: start_address
                str(shipment.end_address),          # H: end_address
                str(shipment.points_count),         # I: points_count
                str(shipment.distance),             # J: distance
                str(shipment.cost),                 # K: cost
                str(shipment.vehicle),              # L: vehicle
                str(shipment.driver),               # M: driver
                str(shipment.status),               # N: status
                str(shipment.booked_by or ''),      # O: booked_by
                booked_at_str                       # P: booked_at
            ]

            rows_to_add.append(row)

        # Clear existing data (except headers) and add new data
        print("📝 Writing to Google Sheets...")

        try:
            # Get the sheet
            sheet = sheet_manager.sheet

            # Clear all data except first row (headers)
            all_values = sheet.get_all_values()
            if len(all_values) > 1:
                # Delete rows from 2 to end
                sheet.delete_rows(2, len(all_values))
                print(f"   Cleared {len(all_values)-1} old row(s)")

            # Add all new rows at once
            if rows_to_add:
                sheet.append_rows(rows_to_add, value_input_option='USER_ENTERED')
                print(f"   Added {len(rows_to_add)} row(s)")

            print("\n✅ Export completed successfully!")
            print(f"\n📊 Summary:")
            print(f"   Total shipments exported: {len(shipments)}")
            print(f"   Available: {sum(1 for s in shipments if s.status == 'available')}")
            print(f"   Booked: {sum(1 for s in shipments if s.status == 'booked')}")

        except Exception as e:
            print(f"\n❌ Error writing to Google Sheets: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(export_shipments())
