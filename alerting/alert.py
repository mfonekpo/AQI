import requests
import os
from dotenv import load_dotenv


load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")

def send_telegram_alert(message: str):
    if not telegram_token:
        raise EnvironmentError(
            "Missing required environment variable TELEGRAM_TOKEN. Please check the .env file."
        )
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "text": message
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to send Telegram alert: {response.text}")
