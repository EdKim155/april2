"""Script to seed Google Sheets table with test data."""

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.google_sheets.manager import GoogleSheetManager
from bot.config import GOOGLE_SHEET_NAME

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Test data templates
LOADING_POINTS = [
    'РЦ Челябинск',
    'РЦ Екатеринбург',
    'РЦ Пермь',
    'РЦ Уфа',
    'РЦ Тюмень',
    'РЦ Курган',
    'РЦ Оренбург'
]

DIRECTIONS = [
    'Арамиль',
    'Кунашак',
    'Сысерть',
    'Екатеринбург',
    'Челябинск',
    'Пермь',
    'Уфа',
    'Тюмень',
    'Курган',
    'Оренбург',
    'Магнитогорск',
    'Златоуст'
]

CITIES = [
    'Челябинск', 'Екатеринбург', 'Пермь', 'Уфа', 'Тюмень',
    'Курган', 'Оренбург', 'Магнитогорск', 'Златоуст', 'Сысерть',
    'Арамиль', 'Кунашак', 'Миасс', 'Копейск', 'Саткинский район'
]

STREETS = [
    'Тимирязева', 'Ленина', 'Мира', 'Победы', 'Советская',
    'Коммунистическая', 'Гагарина', '8 Марта', 'Кирова', 'Пушкина'
]

VEHICLES = [
    'БЕЛАВА 1220W0 М113ЕУ774',
    'КАМАЗ 5432 А123БВ777',
    'МАН 1234 В456ГД777',
    'DAF 5678 Е789ЖЗ777',
    'VOLVO 9012 И012КЛ777',
    'SCANIA 3456 М456НО777',
    'МЕРСЕДЕС 7890 П901РС777'
]

DRIVERS = [
    'Ворошилов Евгений Юрьевич',
    'Иванов Иван Иванович',
    'Петров Петр Петрович',
    'Сидоров Сидор Сидорович',
    'Кузнецов Кузьма Кузьмич',
    'Смирнов Смирный Смирнович',
    'Попов Поп Попович',
    'Васильев Василий Васильевич',
    'Соколов Сокол Соколович',
    'Лебедев Лебедь Лебедевич'
]

COST_FORMATS = [
    '{distance} км.км',
    '{distance} руб',
    '{distance} руб/км',
    'По договоренности'
]


def generate_shipment_id(index: int) -> str:
    """Generate unique shipment ID."""
    return f"5000{2500 + index:04d}"


def generate_address(city: str, street: str = None) -> str:
    """Generate realistic address."""
    street = street or random.choice(STREETS)
    house_number = random.randint(1, 150)
    return f"{city}, {street}, {house_number}"


def generate_test_shipments(count: int = 10) -> list:
    """
    Generate test shipment data for Google Sheets.
    
    Args:
        count: Number of shipments to generate
        
    Returns:
        List of lists representing rows for Google Sheets
    """
    rows = []
    base_date = datetime.utcnow()
    
    for i in range(count):
        # Generate loading date (between tomorrow and 30 days ahead)
        days_ahead = random.randint(1, 30)
        loading_date = base_date + timedelta(days=days_ahead)
        loading_date = loading_date.replace(
            hour=random.randint(8, 18),
            minute=random.choice([0, 15, 30, 45])
        )
        
        # Generate addresses
        start_city = random.choice(CITIES)
        end_city = random.choice([c for c in CITIES if c != start_city])
        start_address = generate_address(start_city)
        end_address = generate_address(end_city)
        
        # Calculate distance
        distance = random.randint(100, 1500)
        
        # Format loading date as string
        loading_date_str = loading_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Generate row data (columns A-M)
        row = [
            generate_shipment_id(i),          # A: shipment_id
            random.choice(LOADING_POINTS),    # B: loading_point
            loading_date_str,                  # C: loading_date
            random.choice(DIRECTIONS),         # D: direction
            round(random.uniform(0.5, 25.0), 2),  # E: weight
            round(random.uniform(5.0, 120.0), 2), # F: volume
            start_address,                    # G: start_address
            end_address,                      # H: end_address
            random.randint(5, 50),            # I: points_count
            distance,                         # J: distance
            random.choice(COST_FORMATS).format(distance=distance),  # K: cost
            random.choice(VEHICLES),          # L: vehicle
            random.choice(DRIVERS),           # M: driver
            'available',                      # N: status (default)
            '',                               # O: booked_by (empty)
            ''                                # P: booked_at (empty)
        ]
        
        rows.append(row)
    
    return rows


def seed_google_sheet(count: int = 10) -> None:
    """
    Seed Google Sheets table with test data.
    
    Args:
        count: Number of test shipments to create
    """
    logger.info(f"🚀 Starting to seed {count} test shipments to Google Sheets...")
    
    try:
        # Initialize Google Sheets manager
        manager = GoogleSheetManager()
        logger.info("✅ Google Sheets connection established")
        
        # Get existing records to check if we need to add headers
        existing_records = manager.get_all_records()
        
        # Generate test data
        test_rows = generate_test_shipments(count)
        
        # If sheet is empty, add headers first
        if not existing_records:
            headers = [
                'shipment_id', 'loading_point', 'loading_date', 'direction',
                'weight', 'volume', 'start_address', 'end_address',
                'points_count', 'distance', 'cost', 'vehicle', 'driver',
                'status', 'booked_by', 'booked_at'
            ]
            manager.sheet.append_row(headers, value_input_option='USER_ENTERED')
            logger.info("✅ Added headers to Google Sheet")
        
        # Add test data rows
        inserted_count = 0
        for row in test_rows:
            try:
                manager.sheet.append_row(row, value_input_option='USER_ENTERED')
                inserted_count += 1
                logger.info(f"✅ Added shipment: {row[0]} - {row[3]}")
            except Exception as e:
                logger.error(f"❌ Failed to add shipment {row[0]}: {e}")
                continue
        
        logger.info(f"🎉 Successfully seeded {inserted_count} shipments to Google Sheets!")
        
    except Exception as e:
        logger.error(f"❌ Failed to seed Google Sheets: {e}")
        raise


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed Google Sheets table with test data')
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of test shipments to create (default: 10)'
    )
    
    args = parser.parse_args()
    
    seed_google_sheet(count=args.count)


if __name__ == '__main__':
    main()







