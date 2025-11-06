"""Script to seed shipments table with test data."""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bot.database.connection import get_db_session, init_db
from bot.database.crud import create_shipment

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


def generate_test_shipments(count: int = 10) -> List[Dict]:
    """
    Generate test shipment data.
    
    Args:
        count: Number of shipments to generate
        
    Returns:
        List of shipment dictionaries
    """
    shipments = []
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
        
        # Calculate distance (rough estimate between cities)
        distance = random.randint(100, 1500)
        
        # Generate shipment data
        shipment_data = {
            'shipment_id': generate_shipment_id(i),
            'loading_point': random.choice(LOADING_POINTS),
            'loading_date': loading_date,
            'direction': random.choice(DIRECTIONS),
            'weight': Decimal(str(round(random.uniform(0.5, 25.0), 2))),
            'volume': Decimal(str(round(random.uniform(5.0, 120.0), 2))),
            'start_address': start_address,
            'end_address': end_address,
            'points_count': random.randint(5, 50),
            'distance': distance,
            'cost': random.choice(COST_FORMATS).format(distance=distance),
            'vehicle': random.choice(VEHICLES),
            'driver': random.choice(DRIVERS),
            'status': random.choice(['available', 'available', 'available', 'booked']),  # 75% available
            'booked_by': None,
            'booked_at': None,
            'publication_date': base_date - timedelta(days=random.randint(0, 7)),
            'synced_from_sheet': False
        }
        
        # If booked, add booking info
        if shipment_data['status'] == 'booked':
            shipment_data['booked_by'] = f'@test_user_{random.randint(1, 5)}'
            booked_days_ago = random.randint(0, 3)
            shipment_data['booked_at'] = base_date - timedelta(days=booked_days_ago)
        
        shipments.append(shipment_data)
    
    return shipments


async def seed_shipments(count: int = 10) -> None:
    """
    Seed shipments table with test data.
    
    Args:
        count: Number of test shipments to create
    """
    logger.info(f"🚀 Starting to seed {count} test shipments...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise
    
    # Generate test data
    shipments = generate_test_shipments(count)
    
    # Insert shipments
    async with get_db_session() as session:
        inserted_count = 0
        for shipment_data in shipments:
            try:
                await create_shipment(session, shipment_data)
                inserted_count += 1
                logger.info(f"✅ Created shipment: {shipment_data['shipment_id']} - {shipment_data['direction']}")
            except Exception as e:
                logger.error(f"❌ Failed to create shipment {shipment_data['shipment_id']}: {e}")
                continue
    
    logger.info(f"🎉 Successfully seeded {inserted_count} shipments!")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Seed shipments table with test data')
    parser.add_argument(
        '--count',
        type=int,
        default=10,
        help='Number of test shipments to create (default: 10)'
    )
    
    args = parser.parse_args()
    
    await seed_shipments(count=args.count)


if __name__ == '__main__':
    asyncio.run(main())


