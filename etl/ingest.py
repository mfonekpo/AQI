from dotenv import load_dotenv
from etl.fetch import fetch_air_quality
from etl.storage import write_to_bucket
from etl.validate import AirqualityFetchError
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert


load_dotenv()

def ingest_to_bucket():
    """
    Orchestration layer — only responsibility is orchestrating the fetch,
    validate, and storage layers. Has zero knowledge of the inner workings
    of any of those layers.
    """

    try:
        raw_data = fetch_air_quality()
        logger.info("Data fetched from weather API successfully")
        send_telegram_alert("Data fetched from weather API successfully")
    except AirqualityFetchError as e:
        logger.error(f"Failed to fetch air quality data: {e}")
        send_telegram_alert(f"Failed to fetch air quality data: {e}")
        return
    try:
        write_to_bucket(raw_data)
        logger.info("Data saved to staging bucket successfully")
        send_telegram_alert("Data saved to staging bucket successfully")
    except Exception as e:
        logger.error(f"Failed to save data to staging bucket: {e}")
        send_telegram_alert(f"Failed to save data to staging bucket: {e}")
        raise
    except ConnectionError as e:
        logger.error(f"Connection error while saving data to staging bucket: {e}")
        send_telegram_alert(f"Connection error while saving data to staging bucket: {e}")
        raise

if __name__ == "__main__":
    ingest_to_bucket()
