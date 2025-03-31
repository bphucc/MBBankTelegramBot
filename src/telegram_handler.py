import logging
import telegram
from telegram.constants import ParseMode
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID

# Initialize the Telegram bot
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

async def send_bot_message(message):
    """Send message via Telegram bot to the specified group"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_GROUP_ID:
        logging.error("Telegram bot configuration missing. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_GROUP_ID")
        return

    try:
        # Send message to the Telegram group
        await bot.send_message(
            chat_id=TELEGRAM_GROUP_ID,
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logging.info(f"Bot message sent successfully to group {TELEGRAM_GROUP_ID}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {str(e)}")