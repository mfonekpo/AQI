import requests
import json
from dotenv import load_dotenv
import os
from utils.logging_conf import logger
from utils.supabase_conf import create_s3_client
from datetime import datetime
from zoneinfo import ZoneInfo
from tenacity import retry, stop_after_attempt, wait_exponential
from pydantic import BaseModel, field_validator, ValidationError


load_dotenv()


WEATHERAPI = os.getenv("WEATHERAPI")
LAT = os.getenv("LAT")
LONG = os.getenv("LONG")

if not all([WEATHERAPI, LAT, LONG]):
    raise EnvironmentError(
        "Missing required environment variables. Please check the .env file."
        "WEATHERAPI, LAT, LONG must all be set"
    )


url = "http://api.openweathermap.org/data/2.5/air_pollution"

class AirqualityFetchError(Exception):
    pass

class AirQualityReading(BaseModel):
    aqi: int
    date: int
    co_value: float
    ozone_value: float

    @field_validator("aqi")
    def aqi_must_be_in_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError(f"AQI value {v} is outside expected range 1-5")
        return v

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_air_pollution_data():
    payload = {
    "lat": LAT,
    "lon": LONG,
    "appid": WEATHERAPI
}

    try:
        response = requests.get(
        url,
        params=payload,
        timeout=(30, 30)
        )
        response.raise_for_status()
        resp_dict = response.json().get("list", [])[0]

    except requests.exceptions.Timeout:
        logger.error("The request timed out")
        raise AirqualityFetchError("The request timed out")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise AirqualityFetchError(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
        raise AirqualityFetchError(f"Request failed: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
        raise AirqualityFetchError("Failed to decode JSON response")
    else:
        logger.info("Request was successful")

        aqi = resp_dict.get("main", {}).get("aqi", None)
        date = resp_dict.get("dt", None)
        co_value = resp_dict.get("components", {}).get("co", None)
        ozone_value = resp_dict.get("components", {}).get("o3", None)

        try:
            reading = AirQualityReading(
                aqi=aqi,
                date=date,
                co_value=co_value,
                ozone_value=ozone_value
            )
        except ValidationError as e:
            logger.error(f"data validation failed: {e}")
            raise AirqualityFetchError(f"Data Validation failed: {e}")

        return reading.model_dump()


def ingest_to_bucket():
    try:
        data = get_air_pollution_data()
    except AirqualityFetchError as e:
        logger.error(f"Failed to ingest data to bucket: {e}")
        return
    
    s3_client = create_s3_client()
    bucket_name = "raw"
    now = datetime.now(ZoneInfo("Africa/Lagos"))
    time_part = now.strftime("%Y%m%d_%H")
    key=f"raw_data/year={now.year}/month={now.month:02}/day={now.day:02}/hour={now.hour:02}/aqi.json"
    json_bytes = json.dumps(data, indent=4).encode('utf-8')
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key = key,
            Body=json_bytes,
        )
        logger.info(f"data saved at {time_part} to {key}")
    except Exception as e:
        logger.error(f"Failed to ingest data to bucket: {e}")

if __name__ == "__main__":
    ingest_to_bucket()
