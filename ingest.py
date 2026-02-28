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

def get_air_pollution_data():
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
    except response.status_code != 200:
        logger.error(f"Request failed with status code: {response.status_code}")
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

        return json_data


def ingest_to_bucket():
    data = get_air_pollution_data()
    if data:
        with open("air_pollution_data.json", "w") as json_file:
            json.dump(data, json_file)
        logger.info("Data ingested to bucket successfully")
    else:
        logger.error("Failed to ingest data to bucket")


if __name__ == "__main__":
    ingest_to_bucket()
