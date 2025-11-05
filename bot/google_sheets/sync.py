"""Synchronization module for Google Sheets and database."""

import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.crud import get_all_shipment_ids, create_shipment
from bot.google_sheets.manager import GoogleSheetManager

logger = logging.getLogger(__name__)


async def sync_from_google_sheet(session: AsyncSession, sheet_manager: GoogleSheetManager) -> List[str]:
    """
    Synchronize shipments from Google Sheet to database.

    Args:
        session: Database session
        sheet_manager: Google Sheets manager instance

    Returns:
        List[str]: List of new shipment IDs added
    """
    try:
        # Get existing shipment IDs from database
        existing_ids = await get_all_shipment_ids(session)

        # Check for new shipments in Google Sheet
        new_shipments = sheet_manager.check_for_new_shipments(existing_ids)

        if not new_shipments:
            return []

        # Add new shipments to database
        added_ids = []
        for shipment_record in new_shipments:
            try:
                shipment_data = parse_shipment_record(shipment_record)
                await create_shipment(session, shipment_data)
                added_ids.append(shipment_data['shipment_id'])
                logger.info(f"✅ Added new shipment: {shipment_data['shipment_id']}")
            except Exception as e:
                logger.error(f"❌ Error adding shipment {shipment_record.get('shipment_id')}: {e}")
                continue

        if added_ids:
            logger.info(f"🎉 Synchronized {len(added_ids)} new shipments from Google Sheet")

        return added_ids

    except Exception as e:
        logger.error(f"❌ Error during synchronization: {e}")
        return []


def parse_shipment_record(record: Dict) -> Dict:
    """
    Parse shipment record from Google Sheet format to database format.

    Args:
        record: Raw record from Google Sheet

    Returns:
        Dict: Parsed shipment data for database
    """
    # Parse loading_date
    loading_date_str = record.get('loading_date', '')
    try:
        if isinstance(loading_date_str, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S', '%Y-%m-%d', '%d.%m.%Y']:
                try:
                    loading_date = datetime.strptime(loading_date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                loading_date = datetime.utcnow()
        else:
            loading_date = loading_date_str
    except Exception:
        loading_date = datetime.utcnow()

    # Parse weight and volume
    try:
        weight = float(record.get('weight', 0))
    except (ValueError, TypeError):
        weight = 0.0

    try:
        volume = float(record.get('volume', 0))
    except (ValueError, TypeError):
        volume = 0.0

    # Parse points_count and distance
    try:
        points_count = int(record.get('points_count', 0))
    except (ValueError, TypeError):
        points_count = 0

    try:
        distance = int(record.get('distance', 0))
    except (ValueError, TypeError):
        distance = 0

    shipment_data = {
        'shipment_id': str(record.get('shipment_id', '')),
        'loading_point': str(record.get('loading_point', '')),
        'loading_date': loading_date,
        'direction': str(record.get('direction', '')),
        'weight': weight,
        'volume': volume,
        'start_address': str(record.get('start_address', '')),
        'end_address': str(record.get('end_address', '')),
        'points_count': points_count,
        'distance': distance,
        'cost': str(record.get('cost', '')),
        'vehicle': str(record.get('vehicle', '')),
        'driver': str(record.get('driver', '')),
        'status': str(record.get('status', 'available')),
        'booked_by': None,
        'booked_at': None,
        'publication_date': datetime.utcnow(),
        'synced_from_sheet': True
    }

    return shipment_data
