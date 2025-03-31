# MB Bank Transaction Monitor

## Overview

MB Bank Transaction Monitor is a Python-based application that monitors MB Bank account transactions and sends real-time notifications to a Telegram group. The application checks for incoming transactions during configured operating hours, sends notifications when new transactions are detected, provides daily transaction summaries, and includes weather updates.



<img alt="MBBank Transaction Monitor" src="https://thumbs2.imgbox.com/dc/c9/3Vdwb9Ew_t.png" width="300"><img alt="MBBank Transaction Monitor" src="https://images2.imgbox.com/96/b5/Jgp4dWbo_o.png" width="300"><img alt="MBBank Transaction Monitor" src="https://thumbs2.imgbox.com/ba/04/oCuZRWPH_t.png" width="300"> 





## Features

- 🔄 **Real-time transaction monitoring**: Automatically checks for new transactions at regular intervals
- 💬 **Telegram notifications**: Sends formatted notifications about new transactions to a Telegram group
- 📊 **Daily summaries**: Provides end-of-day transaction summaries
- 🌤️ **Weather updates**: Integrates with WeatherAPI to provide periodic weather reports
- ⏱️ **Operating hours**: Operates only during configurable time windows to reduce unnecessary API calls
- 🔁 **Auto-retry**: Implements retry mechanism for API failures
- 📝 **Logging**: Comprehensive logging with automatic log rotation

## Project Structure

```
MBBankTelegram/
├── .env                   # Environment configuration file, start from here
├── last_transaction.json  # Stores the most recent transaction to check if there is a new one
├── main.py                # Main application entry point
├── mb-monitor.service     # Systemd service file for Linux
├── requirements.txt       # Python dependencies
├── run_mb_monitor.sh      # Bash script to run the application
└── src/                   # Source code modules
  ├── bank_api.py          # MB Bank API client implementation
  ├── config.py            # Application configuration
  ├── mbbank_patch.py      # Patches for the MBBank library
  ├── telegram_handler.py  # Telegram messaging functionality
  ├── test.py              # Test utility for verifying components after configuration
  ├── transaction.py       # Transaction processing logic
  ├── utils.py             # Utility functions
  └── weather_service.py   # Weather API integration
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Pip package manager
- Virtual environment (recommended)
- Telegram bot token (obtained from [@BotFather](https://telegram.me/BotFather))
- MB Bank account credentials

### Installation

1. Clone or download the repository:

   ```bash
   git clone https://github.com/bphucc/MBBankTelegram.git
   
   cd MBBankTelegram
   ```

1. Create a virtual environment and activate it:

   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

1. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

1. Create a `.env` file with your configuration:

   ```
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   
   TELEGRAM_GROUP_ID="your_telegram_group_id"
   
   WEATHER_API_KEY="your_weather_api_key"
   
   WEATHER_COORDINATES="lat_long_of_your_desired_location"
   
   ACCOUNT_INFO="your_account_number MBBank"
   ```

### Configuration

The application is configured using the `.env` file and the `config.py` module. Here are the key configuration options:

#### Environment Variables (in `.env`file)

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `TELEGRAM_GROUP_ID`: ID of your Telegram group (must start with a minus sign if it's a group)
- `WEATHER_API_KEY`: API key from [WeatherAPI](https://www.weatherapi.com/)
- `ACCOUNT_INFO`: Your account information to display in notifications

#### Application Settings (in `config.py`)

- `WEATHER_CHECK_INTERVAL`: How often to update weather (in seconds)
- `OPERATING_START_HOUR` and `OPERATING_START_MINUTE`: When to start monitoring each day
- `OPERATING_END_HOUR` and `OPERATING_END_MINUTE`: When to stop monitoring each day
- `CHECK_INTERVAL_SECONDS`: How often to check for new transactions
- `CONSOLE_CLEAR_INTERVAL`: How often to refresh the console display

### Testing

Before running the application continuously, it's recommended to run the test script to verify that everything is working correctly:

```python
python src/test.py your_username your_password
```

This will test connectivity to MB Bank, transaction retrieval, weather updates, and Telegram messaging.

### Running on Linux

#### Using the Shell Script

The application can be run directly using the provided shell script:

```bash
chmod +x run_mb_monitor.sh

./run_mb_monitor.sh your_username your_password
```



#### Setting up as a Systemd Service

For continuous operation on Linux, you can set up the application as a systemd service:

1. Edit the `mb-monitor.service` file to update the paths and credentials:

   ```bash
   [Unit]
   
   Description=MB Bank Transaction Monitor
   
   After=network.target
   
   [Service]
   
   Type=simple
   
   User=your_username
   
   WorkingDirectory=/path/to/MBBankTelegram/
   
   ExecStart=/bin/bash /path/to/MBBankTelegram/run_mb_monitor.sh your_mb_username your_mb_password
   
   Restart=always
   
   RestartSec=10
   
   StandardOutput=append:/path/to/MBBankTelegram/mb_monitor_output.log
   
   StandardError=append:/path/to/MBBankTelegram/mb_monitor_error.log
   
   [Install]
   
   WantedBy=multi-user.target
   ```

2. Copy the service file to the systemd directory and enable it:

   ```bash
   sudo cp mb-monitor.service /etc/systemd/system/
   
   sudo systemctl daemon-reload
   
   sudo systemctl enable mb-monitor.service
   
   sudo systemctl start mb-monitor.service
   ```

3. Check the status of the service:

   ```bash
   sudo systemctl status mb-monitor.service
   ```

4. View logs:

   ```bash
   # Application logs
   
   tail -f mb_transaction_monitor.log
   
   # Systemd service logs
   
   sudo systemctl status mb-monitor
   ```

## How It Works

### Transaction Monitoring

The application periodically checks for new transactions during configured operating hours. When a new transaction is detected, it:

1. Compares it with the last known transaction stored in `last_transaction.json`
2. If it's a new transaction, formats a notification message
3. Sends the notification to the configured Telegram group
4. Updates the stored transaction record

### Daily Summaries

At the end of the operating hours each day, the application:

1. Retrieves all transactions for the day
2. Calculates the total number of transactions and total amount
3. Formats a summary message
4. Sends it to the Telegram group

### Weather Updates

The application periodically fetches weather information and sends it to the Telegram group:

1. When entering operating hours (morning message)
2. At regular intervals defined by `WEATHER_CHECK_INTERVAL`

### Operating Hours

The application only performs transaction checks during the configured operating hours to reduce unnecessary API calls and potential rate limiting. When entering operating hours, it sends a greeting message, and when exiting, it sends a daily summary followed by a goodnight message.

### Error Handling

The application includes robust error handling:

- Automatic retry for common API errors (503, connection issues)
- Graceful handling of temporary unavailability
- Comprehensive logging of errors and warnings
- Notification of critical errors via Telegram

## Issues, suggestions
Please kindly open an issue and tell me what's on your mind, so I can fix it either improve it..?

## Security Considerations

- The application requires storing your MB Bank credentials either in the service file or as command-line arguments
- Ensure that the files containing your credentials have appropriate permissions
- Consider running the application in a secure, isolated environment
- Be cautious about exposing your Telegram bot token and group ID

## Troubleshooting

- Check the log files (`mb_transaction_monitor.log`) for detailed error information
- Run the test script to verify individual components
- Ensure your MB Bank credentials are correct
- Verify that your Telegram bot has permission to send messages to the group

## Credits

This project uses the [MBBank](https://github.com/thedtvn/MBBank/) Python library for interacting with MB Bank services. Special thanks to the library's creators for providing this fantastic resource that makes it possible to build applications that integrate with MB Bank.

The project also leverages:

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration
- [WeatherAPI](https://www.weatherapi.com/) for weather data
- [aiohttp](https://github.com/aio-libs/aiohttp) for asynchronous HTTP requests
- [python-dotenv](https://github.com/theskumar/python-dotenv) for environment variable management

## License

📚 This project is provided as-is for educational and personal use. Feel free to use, modify, and do whatever you want with it — just don’t forget to give me credit where it's due. I’ll be forever grateful 🙌. Use responsibly, and may the code be ever in your favor! 🚀

## Disclaimer

This project is not officially affiliated with MB Bank. It is provided for use at your own risk and discretion. The developer disclaim any responsibility for any issues or damages arising from the use of this script. By using the script, you acknowledge that MB Bank may suspend or cancel your bank account as a result of using this script to retrieve responses from the bank's server. I am not liable for any such actions taken by the bank.