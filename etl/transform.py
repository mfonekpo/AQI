"""Transformation utilities for converting raw AQI records into Parquet output.

The module reads validated records from the staging S3 bucket, reshapes them
into the reporting-friendly schema, and persists the resulting artifact into
an S3 transform bucket for downstream analytics use.
"""

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
    """Read a raw AQI JSON object from the staging S3 bucket.

    Args:
        key: The S3 object key to retrieve from the staging bucket.

    Returns:
        A validated dictionary representation of the raw AQI record.

    Raises:
        Exception: If the object cannot be retrieved or the payload fails
            validation.
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
    """Convert an S3 raw AQI record into the analytics-ready schema.

    Args:
        key: The S3 key of the raw AQI JSON object to transform.

    Returns:
        A dict containing the normalized AQI fields, including the epoch date,
        the ISO-8601 UTC timestamp, and the sensor readings.
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

def convert_to_parquet(transformed_data: dict) -> bytes:
    """Serialize a transformed AQI record into Parquet bytes.

    Args:
        transformed_data: A dictionary matching the transformed reading schema.

    Returns:
        The serialized Parquet payload as a byte string.

    Raises:
        Exception: If the transformed payload does not satisfy the domain
            validation rules.
    """

    try:
        # transformed_data = convert_date_from_unix_to_datetime(key)
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
    """Transform a raw AQI object and write the Parquet artifact to S3.

    Args:
        key: The raw object key stored in the staging bucket.

    Returns:
        None.

    Raises:
        Exception: If the transformation or S3 upload fails unexpectedly.
    """

    transformed_record = convert_date_from_unix_to_datetime(key)

    parquet_bytes = convert_to_parquet(transformed_record)

    observation_time = (
        datetime.fromtimestamp(
            transformed_record["date_epoch"], tz=timezone.utc
        )
    )

    bucket_name = "aqi-transform"
    s3_client = create_s3_client()
    observation_time = datetime.fromtimestamp(
        transformed_record["date_epoch"], tz=timezone.utc
    )
    key = (
        f"transformed_data/"
        f"year={observation_time.year}/"
        f"month={observation_time.month:02d}/"
        f"day={observation_time.day:02d}/"
        f"hour={observation_time.hour:02d}/"
        f"aqi.parquet"
    )

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=parquet_bytes,
        )
        logger.info(f"Data successfully ingested to {bucket_name}: {key}")
        logger.info(f"Data saved at {now_wat().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    except Exception as e:
        logger.error(f"Failed to ingest data to {bucket_name}: {e}")
        send_telegram_alert(f"Failed to ingest data to {bucket_name}: {e}")
        raise
