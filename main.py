#!/usr/bin/env python3
import asyncio
import datetime
import json
import sys
import os
import logging
import signal
import time

# Set TERM environment variable if not set
if 'TERM' not in os.environ:
    os.environ['TERM'] = 'xterm-256color'

# Import from our src modules
from src import mbbank_patch
from src.config import (
    CHECK_INTERVAL_SECONDS, CONSOLE_CLEAR_INTERVAL, WEATHER_CHECK_INTERVAL,
    WEATHER_COORDINATES
)
from src.utils import (
    clear_console, print_timestamp, is_within_operating_hours, 
    escape_markdown, get_runtime, save_last_transaction, load_last_transaction
)
from src.telegram_handler import send_bot_message
from src.weather_service import get_weather, format_weather_message
from src.bank_api import create_bank_client
from src.transaction import (
    get_latest_transaction, get_daily_transaction_summary,
    format_notification_message, format_daily_summary_message,
    is_new_transaction
)

# Apply patches before anything else
mbbank_patch.apply_patches()

# Flag to control the main loop
running = True

# Track last console clear time and weather check time
last_console_clear = time.time()
last_weather_check = 0
last_operation_state = None  # To track changes in operating hours status


def signal_handler(sig, frame):
    """Handle termination signals"""
    global running
    logging.info("Received termination signal. Shutting down gracefully...")
    running = False

def flush_log_files():
    """Find and flush all .log files in the current directory"""
    # Get current timestamp for backup files
    timestamp = datetime.datetime.now().strftime("%Y%m%d")

    # Find all .log files in the current directory
    log_files = []
    for file in os.listdir('.'):
        if file.endswith('.log'):
            log_files.append(file)

    if not log_files:
        print(f"[{print_timestamp()}] No log files found to flush.")
        return

    print(f"[{print_timestamp()}] Found {len(log_files)} log files to flush...")

    for log_file in log_files:
        try:
            # Skip if file is empty
            if os.path.getsize(log_file) == 0:
                print(f"[{print_timestamp()}] Skipping empty log file: {log_file}")
                continue

            # Create backup with date suffix
            backup_file = f"{log_file}.{timestamp}"

            # Avoid overwriting existing backups for the same day
            backup_index = 1
            original_backup = backup_file
            while os.path.exists(backup_file):
                backup_file = f"{original_backup}.{backup_index}"
                backup_index += 1

            # Copy contents to backup
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as src:
                with open(backup_file, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

            # Clear the current log file
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"--- Log file cleared at {datetime.datetime.now()} ---\n")

            print(f"[{print_timestamp()}] ✅ Flushed log file: {log_file} → {backup_file}")
            logging.info(f"Log file flushed and backed up to {backup_file}")

        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Failed to flush log file {log_file}: {str(e)}")
            logging.error(f"Failed to flush log file {log_file}: {str(e)}")

    print(f"[{print_timestamp()}] Log rotation complete. {len(log_files)} files processed.")

async def check_transactions(username, password):
    """Check for new transactions and notify if found"""
    global last_console_clear

    # Check if it's time to clear the console
    current_time = time.time()
    if current_time - last_console_clear > CONSOLE_CLEAR_INTERVAL:
        clear_console()
        print(f"[{print_timestamp()}] Console cleared. MB Bank Transaction Monitor running...")
        last_console_clear = current_time

    try:
        # Skip if outside operating hours
        if not is_within_operating_hours():
            logging.debug("Outside operating hours, skipping this check")
            return True  # Continue running

        mb = await create_bank_client(username, password)

        # Query for today only
        today = datetime.datetime.now()
        start_query_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_query_day = today

        print(f"[{print_timestamp()}] Requesting transaction data from MB Bank server...")

        # Get latest transaction
        latest_transaction = await get_latest_transaction(mb, start_query_day, end_query_day)

        # If no transaction found or there was an API error, log and continue
        if not latest_transaction:
            print(f"[{print_timestamp()}] No transaction found or API temporarily unavailable")
            logging.debug("No transaction history found for today or API error occurred")
            return True  # Keep the program running even if API failed

        # Load last saved transaction
        last_transaction = load_last_transaction()

        # Check if this is a new transaction
        if is_new_transaction(latest_transaction, last_transaction):
            ref_no = latest_transaction['refNo']
            print(f"[{print_timestamp()}] New transaction detected! Ref: {ref_no}")
            logging.info(f"New transaction detected: {ref_no}")

            # Save the new transaction
            save_last_transaction(latest_transaction)

            # Format and send notification
            notification_message = format_notification_message(latest_transaction)
            await send_bot_message(notification_message)

            # Output the transaction as JSON as well
            print(json.dumps(latest_transaction, indent=4, ensure_ascii=False))
        else:
            print(f"[{print_timestamp()}] No new transactions. Latest refNo: {latest_transaction['refNo']}")
            logging.debug(f"No new transactions. Latest refNo: {latest_transaction['refNo']}")

        return True  # Continue running

    except Exception as e:
        error_message = f"Error during transaction check: {str(e)}"
        print(f"[{print_timestamp()}] {error_message}")

        # Don't stop the program for temporary connection issues
        if "connection" in str(e).lower() or "timeout" in str(e).lower() or "503" in str(e):
            logging.warning(error_message)
            print(f"[{print_timestamp()}] Temporary connection issue. Will retry on next check.")
            return True  # Continue running despite temporary errors

        # For other more serious errors, log as critical and notify
        logging.critical(error_message, exc_info=True)

        # Notify about critical error through the bot
        error_msg = f"❌ *ERROR* ❌\n\n{escape_markdown(str(e))}\n\nMonitoring stopped at {escape_markdown(str(datetime.datetime.now()))}"

        try:
            await send_bot_message(error_msg)
        except Exception as telegram_err:
            logging.error(f"Failed to send Telegram error message: {str(telegram_err)}")

        return False  # Stop running due to serious error


async def main_async(username, password):
    """Main function with continuous monitoring loop"""
    global running, last_console_clear, last_weather_check, last_operation_state

    # Initialize console clear timer
    last_console_clear = time.time()
    last_weather_check = 0
    last_log_flush_date = datetime.datetime.now().date()

    # Clear console at startup
    clear_console()

    # Register signal handlers for graceful termination
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # termination signal

    # Log startup
    startup_msg = f"🚀 Kiểm tra giao dịch MBBank chạy lúc {datetime.datetime.now()}"
    print(f"[{print_timestamp()}] {startup_msg}")
    logging.info(startup_msg)
    await send_bot_message(escape_markdown(startup_msg))

    # Initial check for operating state
    last_operation_state = is_within_operating_hours()

    # Main monitoring loop
    while running:
        # Check if we should flush logs (once per day at 7:30 AM)
        current_date = datetime.datetime.now().date()
        current_hour = datetime.datetime.now().hour
        current_minute = datetime.datetime.now().minute

        if (current_date > last_log_flush_date and
                current_hour == 7 and
                30 <= current_minute < 35):
            print(f"[{print_timestamp()}] It's 7:30 AM - flushing log files...")
            flush_log_files()
            last_log_flush_date = current_date

        # Check if operating hours status has changed
        current_operation_state = is_within_operating_hours()

        if current_operation_state != last_operation_state:
            if current_operation_state:  # Changed from non-operational to operational
                # Send good morning message
                morning_msg = "🌞 *Chào buổi sáng, một ngày mới tốt lành\\!* 🌞"
                print(f"[{print_timestamp()}] Operating hours began, sending morning message")
                await send_bot_message(morning_msg)

                # Check weather immediately when entering operating hours
                weather_data = await get_weather(WEATHER_COORDINATES)
                if weather_data:
                    weather_msg = format_weather_message(weather_data, get_runtime())
                    await send_bot_message(weather_msg)
                    last_weather_check = time.time()
            else:  # Changed from operational to non-operational
                # Get daily transaction summary first
                print(f"[{print_timestamp()}] Generating daily transaction summary...")
                today = datetime.datetime.now()
                start_query_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
                end_query_day = today

                mb = await create_bank_client(username, password)
                summary = await get_daily_transaction_summary(mb, start_query_day, end_query_day)
                summary_msg = format_daily_summary_message(summary)
                await send_bot_message(summary_msg)

                # Send goodnight message after summary
                goodnight_msg = "😴 *Đã đến giờ đi ngủ, hẹn gặp bạn vào sáng mai\\!* 💤"
                print(f"[{print_timestamp()}] Operating hours ended, sending goodnight message")
                await send_bot_message(goodnight_msg)

            # Update last state
            last_operation_state = current_operation_state

        # Check if we should check weather (every WEATHER_CHECK_INTERVAL)
        current_time = time.time()
        if current_operation_state and (current_time - last_weather_check >= WEATHER_CHECK_INTERVAL):
            print(f"[{print_timestamp()}] Checking weather data...")
            weather_data = await get_weather(WEATHER_COORDINATES)
            if weather_data:
                weather_msg = format_weather_message(weather_data, get_runtime())
                await send_bot_message(weather_msg)
            last_weather_check = current_time

        # Check for transactions only during operating hours
        if current_operation_state:
            continue_running = await check_transactions(username, password)
            if not continue_running:
                logging.error("Error occurred, stopping monitor")
                running = False
                break
        else:
            print(f"[{print_timestamp()}] Outside operating hours, skipping transaction check")

        # Wait before next check
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)

    # Log shutdown
    shutdown_msg = f"🛑 Kiểm tra giao dịch MBBank dừng lúc {datetime.datetime.now()}"
    print(f"[{print_timestamp()}] {shutdown_msg}")
    logging.info(shutdown_msg)
    await send_bot_message(escape_markdown(shutdown_msg))


if __name__ == '__main__':
    """Main entry point for the program"""
    if len(sys.argv) != 3:
        print(json.dumps({"error": "Usage: python main.py <username> <password>"}))
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]

    try:
        asyncio.run(main_async(username, password))
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        print(json.dumps({"error": f"Unhandled exception: {str(e)}"}))
        sys.exit(1)