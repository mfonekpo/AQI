import json
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.logging_conf import logger
from utils.supabase_conf import create_s3_client
from alerting.alert import send_telegram_alert


def build_s3_key(now: datetime) -> str:
    """
    Pure function — builds the S3 key from a datetime.
    Pure functions are the easiest things to test: no mocks needed.
    """
    return(
        f"raw_data/"
        f"year={now.year}/"
        f"month={now.month:02}/"
        f"day={now.day:02}/"
        f"hour={now.hour:02}/"
        f"aqi.json"
    )


def write_to_bucket(data: dict) -> None:
    """
    Storage layer — only responsibility is writing data to S3.
    Has zero knowledge of HTTP or validation.
    Receives already-validated data as a plain dict.
    """

    bucket_name = "aqi-staging"

    s3_client = create_s3_client()
    now = datetime.now(ZoneInfo("Africa/Lagos"))
    key = build_s3_key(now)
    json_bytes = json.dumps(data, indent=4).encode("utf-8")

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_bytes,
        )
        logger.info(f"data saved at {now} to {key}")
        send_telegram_alert(f"Data successfully ingested to {bucket_name}: {key}")
    except Exception as e:
        logger.error(f"Failed to ingest data to {bucket_name}: {e}")
        send_telegram_alert(f"Failed to ingest data to {bucket_name}: {e}")
        raise
