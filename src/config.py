import os
import locale
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram configurations
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')

# Weather configurations
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
WEATHER_COORDINATES = os.getenv('WEATHER_COORDINATES')  # Format: "lat,lon"
WEATHER_CHECK_INTERVAL = 1.5 * 60 * 60  # 1.5 hours in seconds

# Bank configurations
ACCOUNT_INFO = os.getenv('ACCOUNT_INFO')
TRANSACTION_STORE_FILE = "last_transaction.json"
TIMEOUT_SECONDS = 15

# Operating hours
OPERATING_START_HOUR = 7
OPERATING_START_MINUTE = 30
OPERATING_END_HOUR = 22
OPERATING_END_MINUTE = 30

# Application settings
CHECK_INTERVAL_SECONDS = 10
CONSOLE_CLEAR_INTERVAL = 300  # 5 minutes

# Configure logging
logging.basicConfig(
    filename='mb_transaction_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Set Vietnamese locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'vi_VN.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'vi_VN')
    except locale.Error:
        logging.warning("Vietnamese locale not available, using default")