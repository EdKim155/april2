"""Configuration module for April Shipments Bot."""

import os
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', 5432))
DB_NAME = os.getenv('DB_NAME', 'april_bot')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Database URL
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Google Sheets Configuration
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', str(BASE_DIR / 'credentials' / 'google_credentials.json'))
GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Перевозки')
SYNC_INTERVAL = int(os.getenv('SYNC_INTERVAL', 10))  # seconds

# Timezone Configuration
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Europe/Moscow'))

# Scheduler Configuration
PUBLISH_HOUR = int(os.getenv('PUBLISH_HOUR', 11))
PUBLISH_MINUTE = int(os.getenv('PUBLISH_MINUTE', 30))

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Rate Limiting
MAX_BOOKINGS_PER_MINUTE = int(os.getenv('MAX_BOOKINGS_PER_MINUTE', 10))

# Pagination
SHIPMENTS_PER_PAGE = 10

# Logo Configuration
LOGO_PATH = str(BASE_DIR / 'assets' / 'logo.png')
