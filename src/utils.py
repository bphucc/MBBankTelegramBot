import os
import platform
import datetime
import logging
import json
from src.config import TRANSACTION_STORE_FILE

START_TIME = datetime.datetime.now()  # Track application start time

def get_runtime():
    """Calculate the application runtime and return formatted string"""
    current_time = datetime.datetime.now()
    runtime = current_time - START_TIME

    # Extract days, hours, minutes, seconds
    days = runtime.days
    hours, remainder = divmod(runtime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"
def clear_console():
    """Clear the console based on operating system"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def print_timestamp():
    """Print formatted current timestamp"""
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


def is_within_operating_hours():
    """Check if current time is within allowed operating hours"""
    from src.config import OPERATING_START_HOUR, OPERATING_START_MINUTE, OPERATING_END_HOUR, OPERATING_END_MINUTE

    current_time = datetime.datetime.now().time()
    start_time = datetime.time(OPERATING_START_HOUR, OPERATING_START_MINUTE)
    end_time = datetime.time(OPERATING_END_HOUR, OPERATING_END_MINUTE)

    return start_time <= current_time <= end_time


def escape_markdown(text):
    """Escape special characters for Telegram's MarkdownV2 format"""
    if not isinstance(text, str):
        text = str(text)

    # Characters to escape in MarkdownV2: _ * [ ] ( ) ~ ` > # + - = | { } . !
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def format_currency(amount):
    """Format amount as VND currency"""
    try:
        # Try to convert to int if it's a string
        amount_value = int(amount) if amount and amount != "N/A" else 0
        # Format with commas
        formatted = "{:,}".format(amount_value)
        return f"{formatted} VNĐ"
    except (ValueError, TypeError):
        return f"{amount} VNĐ"


def save_last_transaction(transaction):
    """Save last transaction to file"""
    with open(TRANSACTION_STORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(transaction, f, ensure_ascii=False, indent=4)


def load_last_transaction():
    """Load last transaction from file"""
    if not os.path.exists(TRANSACTION_STORE_FILE):
        return None

    try:
        with open(TRANSACTION_STORE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logging.error(f"Error loading last transaction: {e}")
        return None