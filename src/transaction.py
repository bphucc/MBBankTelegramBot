import logging
from src.config import ACCOUNT_INFO
from src.utils import escape_markdown, format_currency, print_timestamp
from src.bank_api import handle_bank_request_with_retry


def is_new_transaction(current, previous):
    """Check if current transaction is new compared to previous"""
    if not previous:
        return True

    # Compare by refNo (primary) and transactionDate (secondary)
    if current['refNo'] != previous['refNo']:
        return True
    if current['transactionDate'] != previous['transactionDate']:
        return True

    return False


def format_notification_message(transaction):
    """Format transaction data for notification message compatible with Telegram's MarkdownV2"""
    # Escape special characters for Markdown
    description = escape_markdown(transaction['description'])
    ref_no = escape_markdown(transaction['refNo'])
    transaction_date = escape_markdown(transaction['transactionDate'])
    amount = escape_markdown(format_currency(transaction['creditAmount']))
    account = escape_markdown(ACCOUNT_INFO)

    return (
        f"💰 *THÔNG BÁO GIAO DỊCH* 💰\n\n"
        f"💸 Tiền vào: *{amount}*\n\n"
        f"🏦 Tài khoản: {account}\n\n"
        f"📝 Nội dung thanh toán: {description}\n\n"
        f"🔢 Mã tham chiếu: {ref_no}\n\n"
        f"⏱ Giao dịch lúc: *{transaction_date}*"
    )


async def get_latest_transaction(mb, start_date, end_date):
    """Get latest transaction with retry and error handling"""

    async def get_transactions():
        return await mb.getTransactionAccountHistory(from_date=start_date, to_date=end_date)

    try:
        # Use our retry handler
        trans = await handle_bank_request_with_retry(get_transactions, max_retries=3, initial_delay=5)

        if trans is None or 'transactionHistoryList' not in trans:
            return None

        if not trans["transactionHistoryList"]:
            return None

        # Get the first (latest) transaction
        latest = trans["transactionHistoryList"][0]

        return {
            "postingDate": latest.get("postingDate", "N/A"),
            "transactionDate": latest.get("transactionDate", "N/A"),
            "creditAmount": latest.get("creditAmount", "N/A"),
            "description": latest.get("description", "N/A"),
            "refNo": latest.get("refNo", "N/A"),
            "transactionType": latest.get("transactionType", "N/A")
        }

    except Exception as e:
        error_message = f"Error getting transaction: {str(e)}"
        if "503" in str(e) or "content type" in str(e).lower():
            error_message = f"MBBank API temporarily unavailable (service maintenance). Will retry on next check."

        logging.error(error_message)
        print(f"[{print_timestamp()}] {error_message}")

        # Don't raise the exception, just return None
        return None


async def get_daily_transaction_summary(mb, start_date, end_date):
    """Get summary of all transactions for a given day with retry logic"""

    async def get_transactions():
        return await mb.getTransactionAccountHistory(from_date=start_date, to_date=end_date)

    try:
        # Use our retry handler
        trans = await handle_bank_request_with_retry(get_transactions, max_retries=3, initial_delay=5)

        if trans is None or 'transactionHistoryList' not in trans or not trans["transactionHistoryList"]:
            return {
                "date": start_date.strftime("%d-%m-%Y"),
                "total_credit": 0,
                "transaction_count": 0
            }

        # Count transactions and sum credit amounts
        transactions = trans["transactionHistoryList"]
        total_credit = sum(int(tx.get("creditAmount", 0) or 0) for tx in transactions)
        transaction_count = len(transactions)

        return {
            "date": start_date.strftime("%d-%m-%Y"),
            "total_credit": total_credit,
            "transaction_count": transaction_count
        }
    except Exception as e:
        logging.error(f"Error getting daily transaction summary: {str(e)}")
        return {
            "date": start_date.strftime("%d-%m-%Y"),
            "total_credit": 0,
            "transaction_count": 0,
            "error": str(e)
        }


def format_daily_summary_message(summary):
    """Format daily transaction summary for a notification message"""
    date = escape_markdown(summary["date"])
    transaction_count = summary["transaction_count"]
    total_amount = escape_markdown(format_currency(summary["total_credit"]))

    if transaction_count > 0:
        message = (
            f"📊 *THỐNG KÊ GIAO DỊCH NGÀY* 📊\n\n"
            f"📅 Ngày: *{date}*\n\n"
            f"🧮 Tổng số giao dịch: *{transaction_count}*\n\n"
            f"💵 Tổng tiền vào: *{total_amount}*\n\n"
        )
    else:
        message = (
            f"📊 *THỐNG KÊ GIAO DỊCH NGÀY* 📊\n\n"
            f"📅 Ngày: *{date}*\n\n"
            f"💬 Không có giao dịch nào hôm nay\\.\n\n"
        )

    return message