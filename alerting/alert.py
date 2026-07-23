"""Notification helpers for posting pipeline health updates to Telegram."""

import requests
import os
from dotenv import load_dotenv


load_dotenv()

telegram_token = os.getenv("TELEGRAM_TOKEN")

def send_telegram_alert(message: str):
    """Send a single text alert to the configured Telegram chat.

    Args:
        message: Human-readable notification content to deliver.

    Raises:
        EnvironmentError: If the Telegram token is not configured.
        RuntimeError: If the Telegram API request does not return success.
    """
    if not telegram_token:
        raise EnvironmentError(
            "Missing required environment variable TELEGRAM_TOKEN. Please check the .env file."
        )
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
        "text": message
    }
    response = requests.post(url, data=data, timeout=(30, 30))
    if response.status_code != 200:
        raise RuntimeError(f"Failed to send Telegram alert: {response.text}")
