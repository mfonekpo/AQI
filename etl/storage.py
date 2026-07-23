"""Storage helpers for persisting raw AQI data into Amazon S3.

The module owns the S3 object-key layout and the S3 write operation for raw
payloads arriving from the producer ingestion flow.
"""

import json
from datetime import datetime, timezone
from utils.logging_conf import logger
from utils.aws_conf import create_s3_client
from alerting.alert import send_telegram_alert


def build_s3_key(now: datetime) -> str:
    """Build a deterministic S3 key for a raw AQI payload.

    Args:
        now: The UTC timestamp that should be encoded into the partition path.

    Returns:
        A path-like S3 key in the ``raw_data/year=.../month=.../day=.../hour=.../aqi.json``
        format.
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
    """Persist an already-validated AQI payload to the staging S3 bucket.

    Args:
        data: A dictionary containing the validated AQI reading payload.

    Raises:
        Exception: If the S3 write operation cannot be completed.
    """

    bucket_name = "aqi-staging"

    s3_client = create_s3_client()
    now = datetime.now(timezone.utc)
    key = build_s3_key(now)
    json_bytes = json.dumps(data, indent=4).encode("utf-8")

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_bytes,
        )
        logger.info(f"data saved at {now} to {key}")
    except Exception as e:
        logger.error(f"Failed to ingest data to {bucket_name}: {e}")
        send_telegram_alert(f"Failed to ingest data to {bucket_name}: {e}")
        raise
