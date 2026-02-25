import requests
import json
from dotenv import load_dotenv
import os
from utils.logging_conf import logger

load_dotenv()

WEATHERAPI = os.getenv("WEATHERAPI")
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")

payload = {
    "lat": LAT,
    "lon": LONG,
    "appid": WEATHERAPI
}

url = "http://api.openweathermap.org/data/2.5/air_pollution"

try:
    response = requests.get(
    url,
    params=payload,
    timeout=(30, 30)
    )
    json_data = response.json()

except requests.exceptions.Timeout:
    logger.ERROR("The request timed out")
except requests.exceptions.RequestException as e:
    logger.ERROR(f"An error occurred: {e}")
except json.JSONDecodeError:
    logger.ERROR("Failed to decode JSON response")
except requests.exceptions.HTTPError as e:
    logger.ERROR(f"HTTP error occurred: {e}")
else:
    logger.INFO("Request was successful")



print(json_data)