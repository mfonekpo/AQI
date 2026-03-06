import requests
import json
from dotenv import load_dotenv
import os
from utils.logging_conf import logger
from utils.supabase_conf import create_s3_client
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


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

def get_air_pollution_data():

    aqi_readings = []
    try:
        response = requests.get(
        url,
        params=payload,
        timeout=(30, 30)
        )
        resp_dict = response.json().get("list", [])[0]

    except requests.exceptions.Timeout:
        logger.error("The request timed out")
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
    else:
        logger.info("Request was successful")

        aqi = resp_dict.get("main", {}).get("aqi", None)
        date = resp_dict.get("dt", None)
        co_value = resp_dict.get("components", {}).get("co", None)
        ozone_value = resp_dict.get("components", {}).get("o3", None)

        json_data = {
            "aqi": aqi,
            "date": date,
            "co_value": co_value,
            "ozone_value": ozone_value
        }

        aqi_readings.append(json_data)
        return aqi_readings


def ingest_to_bucket():
    data = get_air_pollution_data()
    s3_client = create_s3_client()
    bucket_name = "lake"
    time_part = datetime.now(
        ZoneInfo("Africa/Lagos")
    ).strftime("%Y-%m-%d_%I-%p")
    if data:
        json_bytes = json.dumps(data, indent=4)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=f"raw_data/aqi_{time_part}.json",
            Body=json_bytes
        )
        logger.info("Data ingested to bucket successfully")
    else:
        logger.error("Failed to ingest data to bucket")


if __name__ == "__main__":
    ingest_to_bucket()
