"""Synchronization module for Google Sheets and database."""

import logging
from datetime import datetime
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from bot.database.crud import get_all_shipment_ids, create_shipment
from bot.database.models import Shipment
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

                # Skip if shipment is not available (None returned)
                if shipment_data is None:
                    logger.info(f"⏭️  Skipping non-available shipment: {shipment_record.get('shipment_id')}")
                    continue

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

    # Get status from record
    status = str(record.get('status', 'available')).strip().lower()

    # Only import available shipments (ignore booked ones)
    if status != 'available':
        return None

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
        'status': 'available',
        'booked_by': None,
        'booked_at': None,
        'publication_date': datetime.utcnow(),
        'synced_from_sheet': True
    }

    return shipment_data


async def sync_deletions_from_google_sheet(session: AsyncSession, sheet_manager: GoogleSheetManager) -> int:
    """
    Удаление перевозок из БД, которых больше нет в таблице.
    
    Args:
        session: Database session
        sheet_manager: Google Sheets manager instance
        
    Returns:
        int: Количество удаленных записей
    """
    try:
        # Получаем все ID из таблицы
        all_records = sheet_manager.get_all_records()
        sheet_ids = {str(record.get('shipment_id', '')).strip() for record in all_records if record.get('shipment_id')}
        
        # Получаем все ID из БД
        stmt = select(Shipment.shipment_id)
        result = await session.execute(stmt)
        db_ids = {row[0] for row in result.all()}
        
        # Находим ID, которые есть в БД, но нет в таблице
        ids_to_delete = db_ids - sheet_ids
        
        if not ids_to_delete:
            return 0
        
        # Удаляем перевозки (с каскадным удалением связанных записей)
        deleted_count = 0
        for shipment_id in ids_to_delete:
            # Сначала удаляем связанные bookings
            from bot.database.models import Booking
            bookings_stmt = select(Booking).where(Booking.shipment_id == shipment_id)
            bookings_result = await session.execute(bookings_stmt)
            bookings = bookings_result.scalars().all()
            for booking in bookings:
                await session.delete(booking)
            
            # Теперь удаляем саму перевозку
            stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
            result = await session.execute(stmt)
            shipment = result.scalar_one_or_none()
            
            if shipment:
                await session.delete(shipment)
                deleted_count += 1
                logger.info(f"🗑️  Удалена перевозка {shipment_id} (нет в таблице)")
        
        if deleted_count > 0:
            await session.commit()
            logger.info(f"✅ Удалено перевозок: {deleted_count}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления перевозок: {e}", exc_info=True)
        await session.rollback()
        return 0


async def sync_statuses_from_google_sheet(session: AsyncSession, sheet_manager: GoogleSheetManager) -> int:
    """
    Синхронизация статусов перевозок из Google Sheets в БД.
    Обновляет статусы существующих перевозок согласно данным в таблице.
    
    Args:
        session: Database session
        sheet_manager: Google Sheets manager instance
        
    Returns:
        int: Количество обновленных записей
    """
    try:
        # Получаем все записи из таблицы
        all_records = sheet_manager.get_all_records()
        if not all_records:
            return 0
        
        updated_count = 0
        
        # Проходим по всем записям из таблицы
        for record in all_records:
            shipment_id = str(record.get('shipment_id', '')).strip()
            if not shipment_id:
                continue
            
            # Получаем статус из таблицы
            sheet_status = str(record.get('status', 'available')).strip().lower()
            
            # Проверяем, есть ли такая перевозка в БД
            stmt = select(Shipment).where(Shipment.shipment_id == shipment_id)
            result = await session.execute(stmt)
            db_shipment = result.scalar_one_or_none()
            
            if not db_shipment:
                continue
            
            # Если статусы различаются - обновляем БД
            if db_shipment.status != sheet_status:
                logger.info(f"🔄 Обновление статуса перевозки {shipment_id}: {db_shipment.status} → {sheet_status}")
                
                if sheet_status == 'booked':
                    # Обновляем на "booked"
                    db_shipment.status = 'booked'
                    db_shipment.booked_by = str(record.get('booked_by', '')).strip() or None
                    
                    # Парсим дату бронирования
                    booked_at_str = str(record.get('booked_at', '')).strip()
                    if booked_at_str:
                        try:
                            for fmt in ['%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S']:
                                try:
                                    db_shipment.booked_at = datetime.strptime(booked_at_str, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            db_shipment.booked_at = datetime.utcnow()
                    
                elif sheet_status == 'available':
                    # Обновляем на "available"
                    db_shipment.status = 'available'
                    db_shipment.booked_by = None
                    db_shipment.booked_at = None
                
                updated_count += 1
        
        if updated_count > 0:
            await session.commit()
            logger.info(f"✅ Синхронизировано статусов: {updated_count}")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"❌ Ошибка синхронизации статусов: {e}", exc_info=True)
        await session.rollback()
        return 0
