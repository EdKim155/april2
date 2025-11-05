"""Google Sheets manager for handling spreadsheet operations."""

import logging
from datetime import datetime
from typing import List, Dict, Optional
import gspread
from google.oauth2.service_account import Credentials

from bot.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME

logger = logging.getLogger(__name__)


class GoogleSheetManager:
    """Manager for Google Sheets operations."""

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    COLUMN_MAPPING = {
        'shipment_id': 1,      # A
        'loading_point': 2,     # B
        'loading_date': 3,      # C
        'direction': 4,         # D
        'weight': 5,            # E
        'volume': 6,            # F
        'start_address': 7,     # G
        'end_address': 8,       # H
        'points_count': 9,      # I
        'distance': 10,         # J
        'cost': 11,             # K
        'vehicle': 12,          # L
        'driver': 13,           # M
        'status': 14,           # N
        'booked_by': 15,        # O
        'booked_at': 16         # P
    }

    def __init__(self):
        """Initialize Google Sheets manager."""
        self.credentials = None
        self.gc = None
        self.sheet = None
        self._initialize()

    def _initialize(self):
        """Initialize Google Sheets connection."""
        try:
            self.credentials = Credentials.from_service_account_file(
                GOOGLE_CREDENTIALS_FILE,
                scopes=self.SCOPES
            )
            self.gc = gspread.authorize(self.credentials)
            self.sheet = self.gc.open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_NAME)
            logger.info("✅ Google Sheets connection established successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets: {e}")
            raise

    def _refresh_connection(self):
        """Refresh Google Sheets connection if expired."""
        try:
            if self.credentials.expired:
                self.credentials.refresh()
                self.gc = gspread.authorize(self.credentials)
                self.sheet = self.gc.open_by_key(GOOGLE_SHEET_ID).worksheet(GOOGLE_SHEET_NAME)
                logger.info("🔄 Google Sheets connection refreshed")
        except Exception as e:
            logger.error(f"❌ Failed to refresh connection: {e}")
            self._initialize()

    def get_all_records(self) -> List[Dict]:
        """
        Get all records from the Google Sheet.

        Returns:
            List[Dict]: List of shipment records
        """
        try:
            self._refresh_connection()

            # Check if sheet has any data
            all_values = self.sheet.get_all_values()
            if not all_values or len(all_values) < 2:
                logger.warning("⚠️ Google Sheet is empty or has no data rows (only headers)")
                return []

            # Get records only if we have headers and at least one data row
            records = self.sheet.get_all_records()
            logger.info(f"📊 Retrieved {len(records)} records from Google Sheet")
            return records
        except Exception as e:
            logger.error(f"❌ Error getting all records: {e}", exc_info=True)
            return []

    def update_booking_status(self, shipment_id: str, username: str) -> bool:
        """
        Update booking status in Google Sheet.

        Args:
            shipment_id: Shipment ID to update
            username: Username who booked (without @)

        Returns:
            bool: Success status
        """
        try:
            self._refresh_connection()

            # Find the cell with shipment_id
            cell = self.sheet.find(str(shipment_id))
            if not cell:
                logger.error(f"❌ Shipment {shipment_id} not found in sheet")
                return False

            row = cell.row
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Batch update for efficiency
            updates = [
                {
                    'range': f'N{row}',  # status
                    'values': [['booked']]
                },
                {
                    'range': f'O{row}',  # booked_by
                    'values': [[f'@{username}']]
                },
                {
                    'range': f'P{row}',  # booked_at
                    'values': [[timestamp]]
                }
            ]

            self.sheet.batch_update(updates, value_input_option='USER_ENTERED')
            logger.info(f"✅ Updated booking status for shipment {shipment_id} in Google Sheet")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating booking status: {e}")
            return False

    def cancel_booking(self, shipment_id: str) -> bool:
        """
        Cancel booking in Google Sheet.

        Args:
            shipment_id: Shipment ID to cancel

        Returns:
            bool: Success status
        """
        try:
            self._refresh_connection()

            # Find the cell with shipment_id
            cell = self.sheet.find(str(shipment_id))
            if not cell:
                logger.error(f"❌ Shipment {shipment_id} not found in sheet")
                return False

            row = cell.row

            # Batch update to clear booking info
            updates = [
                {
                    'range': f'N{row}',  # status
                    'values': [['available']]
                },
                {
                    'range': f'O{row}',  # booked_by
                    'values': [['']]
                },
                {
                    'range': f'P{row}',  # booked_at
                    'values': [['']]
                }
            ]

            self.sheet.batch_update(updates, value_input_option='USER_ENTERED')
            logger.info(f"✅ Cancelled booking for shipment {shipment_id} in Google Sheet")
            return True

        except Exception as e:
            logger.error(f"❌ Error cancelling booking: {e}")
            return False

    def check_for_new_shipments(self, existing_ids: List[str]) -> List[Dict]:
        """
        Check for new shipments not in existing IDs.

        Args:
            existing_ids: List of existing shipment IDs

        Returns:
            List[Dict]: List of new shipment records
        """
        try:
            all_records = self.get_all_records()
            new_shipments = []

            for record in all_records:
                shipment_id = str(record.get('shipment_id', ''))
                if shipment_id and shipment_id not in existing_ids:
                    # Set default status if not provided
                    if not record.get('status'):
                        record['status'] = 'available'
                    new_shipments.append(record)

            return new_shipments

        except Exception as e:
            logger.error(f"❌ Error checking for new shipments: {e}")
            return []
