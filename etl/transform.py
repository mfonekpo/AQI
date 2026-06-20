from utils.aws_conf import create_s3_client
from alerting.alert import send_telegram_alert
from datetime import datetime, timezone
from etl.validate import AirQualityTransformedReading
from utils.logging_conf import logger
from utils.time_utils import now_wat
import pandas as pd
from etl.validate import AirQualityReading
import io
import json


def get_data_from_bucket(key: str) -> dict:
    """
    Fetches a JSON object from the S3 bucket given its key.
    """

    bucket_name = "aqi-staging"
    s3_client = create_s3_client()

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        data = response["Body"].read().decode("utf-8")

        parsed_data = json.loads(data)
        validated_data = AirQualityReading(**parsed_data) # Validate the data before returning
        return validated_data.model_dump() # return dict instead of pydantic model val
    except Exception as e:
        logger.error(f"Failed to fetch data from bucket: {e}")
        send_telegram_alert(f"Failed to fetch data from bucket: {e}")
        raise


def convert_date_from_unix_to_datetime(key: str) -> dict:
    """
    Transformation layer — only responsibility is transforming the data.
    Has zero knowledge of HTTP, validation, or storage.
    Receives already-validated data as a plain dict and returns a transformed dict.
    """

    data = get_data_from_bucket(key)

    date_value = datetime.fromtimestamp(data["date"], tz=timezone.utc).isoformat()

    logger.info("Data transformation logic fired")
    send_telegram_alert("Data transformation logic fired")

    return {
        "aqi": data["aqi"],
        "date_epoch": data["date"],
        "date_utc": date_value,
        "co_value": data["co_value"],
        "ozone_value": data["ozone_value"]
    }

def convert_to_parquet(key: str) -> bytes:
    """
    Example of a more complex transformation function that converts the data to Parquet format.
    """

    try:
        transformed_data = convert_date_from_unix_to_datetime(key)
        AirQualityTransformedReading(**transformed_data)
    except Exception as e:
        logger.error(f"Data validation failed after transformation: {e}")
        send_telegram_alert(f"Data validation failed after transformation: {e}")
        raise

    df = pd.DataFrame([transformed_data])

    parquet_buffer = io.BytesIO()
    df.to_parquet(parquet_buffer, index=False)

    return parquet_buffer.getvalue()


def save_transformed_data_to_bucket(key: str):
    """
    Orchestration layer — only responsibility is orchestrating the transformation
    and storage layers. Has zero knowledge of the inner workings of either layer.
    """

    # transformed_data = convert_date_from_unix_to_datetime()
    transformed_data = convert_to_parquet(key)

    bucket_name = "aqi-transform"
    s3_client = create_s3_client()
    now = datetime.now(timezone.utc)
    key = f"transformed_data/year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}/aqi.parquet"

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=transformed_data,
        )
        logger.info(f"Data successfully ingested to {bucket_name}: {key}")
        logger.info(f"Data saved at {now_wat().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except Exception as e:
        logger.error(f"Failed to ingest data to {bucket_name}: {e}")
        send_telegram_alert(f"Failed to ingest data to {bucket_name}: {e}")
        raise
