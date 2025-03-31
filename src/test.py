#!/usr/bin/env python3
import asyncio
import sys
import json
import datetime
import logging
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import from our modules
from src.config import WEATHER_COORDINATES, TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID
from src.utils import print_timestamp, is_within_operating_hours
from src.bank_api import create_bank_client
from src.transaction import (
    get_daily_transaction_summary, format_daily_summary_message,
    get_latest_transaction, format_notification_message
)
from src.weather_service import get_weather, format_weather_message

# Conditionally import telegram functions
telegram_available = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_GROUP_ID)
if telegram_available:
    from telegram_handler import send_bot_message

# Apply patches if needed
try:
    import mbbank_patch

    mbbank_patch.apply_patches()
except ImportError:
    print("mbbank_patch not found - continuing without patches")

# Configure simple console logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class MBBankTest:
    """Class to run automated tests for MB Bank Monitor"""
    def __init__(self, username, password):
        """Initialize test with username and password"""
        self.username = username
        self.password = password
        self.send_telegram = False
        self.results = {}
        print(f"Initialized test with username: {username}")

        # Check Telegram configuration
        if telegram_available:
            self.telegram_available = True
            print("✅ Telegram configuration found")
            self.send_telegram = input("Send test messages to Telegram? (y/n): ").lower() == 'y'
            if self.send_telegram:
                print("✓ Will send test messages to Telegram group")
            else:
                print("✓ Will skip sending messages to Telegram")
        else:
            self.telegram_available = False
            self.send_telegram = False
            print("⚠️ Telegram bot token or group ID not set in .env file")
            print("  ↳ Will run tests without sending messages")

    async def send_message(self, message):
        """Send message to Telegram if enabled"""
        if self.send_telegram and telegram_available:
            try:
                await send_bot_message(message)
                print(f"[{print_timestamp()}] ✅ Message sent to Telegram.")
                return True
            except Exception as e:
                print(f"[{print_timestamp()}] ⚠️ Failed to send message: {str(e)}")
                return False
        return None  # Not attempted

    async def test_connection(self):
        """Test basic connection to MB Bank"""
        print(f"\n==== CONNECTION TEST ====")
        try:
            print(f"[{print_timestamp()}] Testing connection to MB Bank...")
            mb = await create_bank_client(self.username, self.password)
            print(f"[{print_timestamp()}] ✅ Connection successful!")
            self.results["connection"] = True
            return True
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Connection failed: {str(e)}")
            self.results["connection"] = False
            return False

    async def test_daily_summary(self):
        """Test daily transaction summary"""
        print(f"\n==== DAILY SUMMARY TEST ====")
        try:
            print(f"[{print_timestamp()}] Testing daily transaction summary...")

            # Create bank client
            mb = await create_bank_client(self.username, self.password)

            # Set up date range for today
            today = datetime.datetime.now()
            start_query_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_query_day = today

            print(f"[{print_timestamp()}] Fetching transactions for {today.strftime('%Y-%m-%d')}...")
            summary = await get_daily_transaction_summary(mb, start_query_day, end_query_day)

            # Print raw summary data
            print(f"[{print_timestamp()}] Raw summary data:")
            print(json.dumps(summary, indent=2, ensure_ascii=False))

            # Format message
            summary_msg = format_daily_summary_message(summary)
            print(f"[{print_timestamp()}] Formatted summary message:")
            print(summary_msg.replace('\\', ''))  # Print without escape chars

            # Send to Telegram if enabled
            await self.send_message(summary_msg)

            self.results["daily_summary"] = True
            return True
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Error in daily summary test: {str(e)}")
            self.results["daily_summary"] = False
            return False

    async def test_latest_transaction(self):
        """Test getting the latest transaction"""
        print(f"\n==== LATEST TRANSACTION TEST ====")
        try:
            print(f"[{print_timestamp()}] Testing latest transaction retrieval...")

            # Create bank client
            mb = await create_bank_client(self.username, self.password)

            # Query for today
            today = datetime.datetime.now()
            start_query_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_query_day = today

            print(f"[{print_timestamp()}] Fetching latest transaction...")
            transaction = await get_latest_transaction(mb, start_query_day, end_query_day)

            if transaction:
                print(f"[{print_timestamp()}] ✅ Latest transaction found:")
                print(json.dumps(transaction, indent=2, ensure_ascii=False))

                # Format notification
                notification = format_notification_message(transaction)
                print(f"[{print_timestamp()}] Formatted transaction notification:")
                print(notification.replace('\\', ''))  # Print without escape chars

                # Send to Telegram if enabled
                await self.send_message(notification)
            else:
                print(f"[{print_timestamp()}] ℹ️ No transactions found for today.")

            self.results["latest_transaction"] = True
            return True
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Error in latest transaction test: {str(e)}")
            self.results["latest_transaction"] = False
            return False

    async def test_weather(self):
        """Test weather service"""
        print(f"\n==== WEATHER TEST ====")
        try:
            print(f"[{print_timestamp()}] Testing weather service...")
            weather_data = await get_weather(WEATHER_COORDINATES)

            if weather_data:
                print(f"[{print_timestamp()}] ✅ Weather data received:")
                print(json.dumps(weather_data["current"], indent=2, ensure_ascii=False))

                # Format weather message
                weather_msg = format_weather_message(weather_data)
                print(f"[{print_timestamp()}] Formatted weather message:")
                print(weather_msg.replace('\\', ''))  # Print without escape chars

                # Send to Telegram if enabled
                await self.send_message(weather_msg)

                self.results["weather"] = True
                return True
            else:
                print(f"[{print_timestamp()}] ❌ Failed to get weather data")
                self.results["weather"] = False
                return False
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Error in weather test: {str(e)}")
            self.results["weather"] = False
            return False

    async def test_specific_date(self):
        """Test transactions for today's date"""
        print(f"\n==== SPECIFIC DATE TRANSACTIONS TEST ====")
        try:
            # Use today's date automatically
            date = datetime.datetime.now()
            print(f"[{print_timestamp()}] Testing transactions for date: {date.strftime('%Y-%m-%d')}...")

            # Create bank client
            mb = await create_bank_client(self.username, self.password)

            # Set up date range
            start_query_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_query_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)

            # Get transactions
            async def get_transactions():
                return await mb.getTransactionAccountHistory(from_date=start_query_day, to_date=end_query_day)

            from bank_api import handle_bank_request_with_retry
            trans = await handle_bank_request_with_retry(get_transactions, max_retries=3, initial_delay=5)

            if not trans or 'transactionHistoryList' not in trans or not trans["transactionHistoryList"]:
                print(f"[{print_timestamp()}] ✅ Test passed but no transactions found for today.")
                self.results["specific_date"] = True
                return True

            # Print transactions
            transactions = trans["transactionHistoryList"]
            print(f"[{print_timestamp()}] ✅ Found {len(transactions)} transactions:")

            # Calculate total credit amount
            total_credit = sum(int(tx.get("creditAmount", 0) or 0) for tx in transactions)
            from utils import format_currency
            print(f"[{print_timestamp()}] Total credit amount: {format_currency(total_credit)}")

            # Print first transaction details
            if transactions:
                print("\nFirst transaction details:")
                print(json.dumps(transactions[0], indent=2, ensure_ascii=False))

                # Print count of other transactions
                if len(transactions) > 1:
                    print(f"\nPlus {len(transactions) - 1} more transactions (not shown)")

            self.results["specific_date"] = True
            return True
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Error in specific date test: {str(e)}")
            self.results["specific_date"] = False
            return False

    async def test_operating_hours(self):
        """Test operating hours check"""
        print(f"\n==== OPERATING HOURS TEST ====")
        try:
            print(f"[{print_timestamp()}] Testing operating hours check...")

            now = datetime.datetime.now()
            is_operating = is_within_operating_hours()

            print(f"[{print_timestamp()}] Current time: {now.strftime('%H:%M:%S')}")
            print(f"[{print_timestamp()}] Within operating hours: {is_operating}")

            # Get details from config
            from config import OPERATING_START_HOUR, OPERATING_START_MINUTE, OPERATING_END_HOUR, OPERATING_END_MINUTE
            print(f"[{print_timestamp()}] Operating hours configuration:")
            print(f"  Start: {OPERATING_START_HOUR:02d}:{OPERATING_START_MINUTE:02d}")
            print(f"  End:   {OPERATING_END_HOUR:02d}:{OPERATING_END_MINUTE:02d}")

            self.results["operating_hours"] = True
            return True
        except Exception as e:
            print(f"[{print_timestamp()}] ❌ Error in operating hours test: {str(e)}")
            self.results["operating_hours"] = False
            return False

    async def run_all_tests(self):
        """Run all available tests automatically"""
        print(f"\n[{print_timestamp()}] 🚀 Running MB Bank Monitor tests...")
        print(f"Current Date and Time (UTC): {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Local Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test connection first
        await self.test_connection()

        # Skip other tests if connection failed
        if not self.results.get("connection", False):
            print(f"\n[{print_timestamp()}] ❌ Connection test failed. Skipping other tests.")
            return self.results

        # Run remaining tests
        await self.test_operating_hours()
        await self.test_weather()
        await self.test_latest_transaction()
        await self.test_daily_summary()
        await self.test_specific_date()

        # Show results
        print("\n==== TEST RESULTS SUMMARY ====")
        for test, result in self.results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test.replace('_', ' ').title()}: {status}")

        # Overall result
        all_passed = all(self.results.values())
        print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

        return self.results


async def main():
    """Main function to run tests"""
    if len(sys.argv) < 3:
        print("Usage: python test.py <username> <password>")
        return

    username = sys.argv[1]
    password = sys.argv[2]

    # Clear screen
    os.system('cls' if os.name == 'nt' else 'clear')

    print(f"==== MB Bank Monitor - Automated Test Utility ====")
    print(f"Current Date and Time (UTC): {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Local Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Username: {username}")

    # Create tester and run all tests
    tester = MBBankTest(username, password)
    await tester.run_all_tests()

    print(f"\n[{print_timestamp()}] Test run complete.")


if __name__ == "__main__":
    asyncio.run(main())