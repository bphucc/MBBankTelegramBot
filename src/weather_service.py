import logging
import aiohttp
from src.config import WEATHER_API_KEY
from src.utils import escape_markdown

async def get_weather(coordinates):
    """Get current weather data"""
    if not WEATHER_API_KEY:
        logging.error("Weather API key missing. Please set WEATHER_API_KEY in .env file.")
        return None

    url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={coordinates}&aqi=no"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logging.error(f"Weather API error: {response.status}, {await response.text()}")
                    return None
    except Exception as e:
        logging.error(f"Error fetching weather: {str(e)}")
        return None

def get_weather_emoji(condition):
    """Get appropriate emoji for weather condition"""
    condition = condition.lower()

    if "sunny" in condition or "clear" in condition:
        return "☀️"
    elif "partly cloudy" in condition:
        return "⛅"
    elif "cloudy" in condition or "overcast" in condition:
        return "☁️"
    elif "rain" in condition or "drizzle" in condition:
        return "🌧"
    elif "thunder" in condition or "lightning" in condition:
        return "⛈"
    elif "snow" in condition:
        return "❄️"
    elif "fog" in condition or "mist" in condition:
        return "🌫"
    else:
        return "🌤"

def format_weather_message(weather_data, runtime = None):
    """Format weather data for a readable message"""
    try:
        location = weather_data["location"]["name"]
        country = weather_data["location"]["country"]
        last_updated = weather_data["current"]["last_updated"]
        temp_c = weather_data["current"]["temp_c"]
        condition_text = weather_data["current"]["condition"]["text"]
        feelslike_c = weather_data["current"]["feelslike_c"]

        # Find emoji for weather condition
        weather_emoji = get_weather_emoji(condition_text)

        message = (
            f"🛰️ *DỰ BÁO THỜI TIẾT* 🛰️\n\n"
            f"📍 Địa điểm: *{escape_markdown(location)}, {escape_markdown(country)}*\n\n"
            f"{weather_emoji} Thời tiết: {weather_emoji} *{escape_markdown(condition_text)} {weather_emoji}*\n\n"
            f"🌡 Nhiệt độ: *{escape_markdown(str(temp_c))}°C*\n\n"
            f"🌡 Cảm giác như: *{escape_markdown(str(feelslike_c))}°C*\n\n"
            f"🕒 Cập nhật lúc: {escape_markdown(last_updated)}\n\n"
            f"⏱️ Thời gian chạy: *{escape_markdown(runtime)}*"
        )
        return message
    except Exception as e:
        logging.error(f"Error formatting weather message: {str(e)}")
        return f"❌ Không thể lấy dữ liệu thời tiết: {escape_markdown(str(e))}"