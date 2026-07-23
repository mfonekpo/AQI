"""Fetch layer for the AQI ingestion pipeline.

This module is responsible for retrieving one current air quality reading from
OpenWeather and validating it against the domain model before it is forwarded
for storage.
"""

import requests
import json
import os
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
from etl.validate import AirQualityReading, AirqualityFetchError
from pydantic import ValidationError


load_dotenv()

WEATHERAPI = os.getenv("WEATHERAPI")
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")

def validate_env():
    """Ensure that all required environment variables are present.

    Raises:
        EnvironmentError: If the OpenWeather credentials or coordinates are not
            configured in the environment.
    """
    if not all([WEATHERAPI, LAT, LONG]):
        raise EnvironmentError(
            "Missing required environment variables. Please check the .env file."
            "WEATHERAPI, LAT, LONG must all be set"
        )

API_URL = "http://api.openweathermap.org/data/2.5/air_pollution"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_air_quality() -> dict:
    """Fetch a validated AQI reading from the OpenWeather API.

    The function performs environment validation, issues a single HTTP request,
    parses the first response record, and ensures that the payload conforms to
    the expected AQI reading schema before returning it.

    Returns:
        A dictionary representing a validated AQI reading payload.

    Raises:
        AirqualityFetchError: If the request fails, the response cannot be
            decoded, or the payload fails schema validation.
    """

    validate_env()

    payload = {
        "lat": LAT,
        "lon": LONG,
        "appid": WEATHERAPI,
    }

    try:
        response = requests.get(API_URL, params=payload, timeout=(30, 30))
        response.raise_for_status()
        resp_dict = response.json().get("list", [])[0]

    except requests.exceptions.Timeout:
        logger.error("The request timed out")
        send_telegram_alert("The request timed out")
        raise AirqualityFetchError("The request timed out")

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        send_telegram_alert(f"HTTP error occurred: {e}")
        raise AirqualityFetchError(f"HTTP error: {e}")

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        send_telegram_alert(f"An error occurred: {e}")
        raise AirqualityFetchError(f"Request failed: {e}")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        send_telegram_alert("Failed to decode JSON response")
        raise AirqualityFetchError("Failed to decode JSON response")

    else:
        logger.info("API request successful")

        aqi = resp_dict.get("main", {}).get("aqi")
        date = resp_dict.get("dt")
        co_value = resp_dict.get("components", {}).get("co")
        ozone_value = resp_dict.get("components", {}).get("o3")

        try:
            reading = AirQualityReading(
                aqi=aqi,
                date=date,
                co_value=co_value,
                ozone_value=ozone_value,
            )
        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            send_telegram_alert(f"Data validation failed: {e}")
            raise AirqualityFetchError(f"Data validation failed: {e}")

        return reading.model_dump()