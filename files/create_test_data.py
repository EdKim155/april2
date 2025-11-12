"""Create test data in Google Sheets with available status."""

from datetime import datetime, timedelta
import random
from bot.google_sheets.manager import GoogleSheetManager


def main():
    """Create test shipments with available status."""
    print("📝 Creating test shipments in Google Sheets...\n")

    sheet_manager = GoogleSheetManager()
    sheet = sheet_manager.sheet

    # Clear existing data (except headers)
    all_values = sheet.get_all_values()
    if len(all_values) > 1:
        sheet.delete_rows(2, len(all_values))
        print(f"   Cleared {len(all_values)-1} old row(s)")

    # Test data
    cities = ['Екатеринбург', 'Курган', 'Челябинск', 'Тюмень', 'Уфа', 'Пермь']
    loading_points = ['РЦ Екатеринбург', 'РЦ Пермь', 'РЦ Челябинск', 'РЦ Курган']
    vehicles = [
        'КАМАЗ 5432 А123БВ777',
        'МЕРСЕДЕС 7890 П901РС777',
        'VOLVO 9012 И012КЛ777',
        'МАН 1234 В456ГД777',
        'SCANIA 3456 М456НО777'
    ]
    drivers = [
        'Иванов Иван Иванович',
        'Петров Петр Петрович',
        'Сидоров Сидор Сидорович',
        'Кузнецов Кузьма Кузьмич',
        'Смирнов Смирный Смирнович'
    ]

    test_shipments = []

    # Create 10 available shipments
    for i in range(10):
        shipment_id = f"TEST{50003000 + i}"
        loading_point = random.choice(loading_points)
        direction = random.choice(cities)
        weight = round(random.uniform(1.0, 25.0), 2)
        volume = round(random.uniform(10.0, 100.0), 2)
        points_count = random.randint(1, 30)
        distance = random.randint(100, 2000)

        # Random cost format
        cost_formats = [f"{distance} руб", f"{distance} км.км", "По договоренности"]
        cost = random.choice(cost_formats)

        vehicle = random.choice(vehicles)
        driver = random.choice(drivers)

        # Loading date - random date in next 30 days
        days_ahead = random.randint(1, 30)
        loading_date = datetime.now() + timedelta(days=days_ahead)
        loading_date_str = loading_date.strftime('%Y-%m-%d %H:%M:%S')

        start_address = f"{direction}, ул. Ленина, {random.randint(1, 200)}"
        end_address = f"{random.choice(cities)}, ул. Мира, {random.randint(1, 200)}"

        row = [
            shipment_id,
            loading_point,
            loading_date_str,
            direction,
            str(weight),
            str(volume),
            start_address,
            end_address,
            str(points_count),
            str(distance),
            cost,
            vehicle,
            driver,
            'available',  # All shipments are available
            '',           # No one booked
            ''            # No booking time
        ]

        test_shipments.append(row)

    # Add all rows at once
    sheet.append_rows(test_shipments, value_input_option='USER_ENTERED')

    print(f"✅ Created {len(test_shipments)} test shipments")
    print("\n📋 Sample shipments:")
    for i, shipment in enumerate(test_shipments[:3], 1):
        print(f"\n   {i}. ID: {shipment[0]}")
        print(f"      Direction: {shipment[3]}")
        print(f"      Loading: {shipment[1]}")
        print(f"      Date: {shipment[2]}")
        print(f"      Status: {shipment[13]}")

    print(f"\n✅ Done! All shipments are available for booking.")


if __name__ == "__main__":
    main()
