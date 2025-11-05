"""Test script to check Google Sheets connection and content."""

import gspread
from google.oauth2.service_account import Credentials
from bot.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def main():
    """Check Google Sheets content."""
    print("🔍 Connecting to Google Sheets...")

    try:
        # Initialize connection
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=SCOPES
        )
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_NAME)

        print(f"✅ Connected to sheet: {GOOGLE_SHEET_NAME}")
        print(f"   Sheet ID: {GOOGLE_SHEET_ID}")

        # Get all values
        all_values = sheet.get_all_values()
        print(f"\n📊 Total rows in sheet: {len(all_values)}")

        if not all_values:
            print("❌ Sheet is completely empty!")
            print("\nℹ️  Please add the following headers in the first row:")
            print("   A: shipment_id")
            print("   B: loading_point")
            print("   C: loading_date")
            print("   D: direction")
            print("   E: weight")
            print("   F: volume")
            print("   G: start_address")
            print("   H: end_address")
            print("   I: points_count")
            print("   J: distance")
            print("   K: cost")
            print("   L: vehicle")
            print("   M: driver")
            print("   N: status")
            print("   O: booked_by")
            print("   P: booked_at")
            return

        # Show first few rows
        print("\n📋 First 3 rows:")
        for i, row in enumerate(all_values[:3]):
            print(f"   Row {i+1}: {row}")

        if len(all_values) >= 2:
            print(f"\n✅ Sheet has {len(all_values)-1} data row(s)")

            # Try to get records
            try:
                records = sheet.get_all_records()
                print(f"✅ Successfully parsed {len(records)} record(s)")

                if records:
                    print("\n📦 First record:")
                    first_record = records[0]
                    for key, value in first_record.items():
                        print(f"   {key}: {value}")
            except Exception as e:
                print(f"❌ Error parsing records: {e}")
        else:
            print("\n⚠️  Sheet only has headers, no data rows")
            print("   Please add at least one shipment to the sheet")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
