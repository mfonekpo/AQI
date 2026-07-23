"""Backfill utilities for replaying existing AQI raw objects through the transform flow.

The module enumerates the raw-data prefix in the staging bucket and reprocesses
historical objects into the transformed bucket to recover or rebuild analytics
artifacts.
"""

from utils.aws_conf import create_s3_client
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
from etl.transform import save_transformed_data_to_bucket

def list_raw_files() -> list[str]:
    """List the raw AQI object keys currently stored in the staging bucket.

    Returns:
        A list of S3 object keys under the ``raw_data/`` prefix.
    """

    bucket_name = "aqi-staging"

    s3_client = create_s3_client()

    response = s3_client.list_objects_v2(
        Bucket=bucket_name,
        Prefix="raw_data/"
    )

    return [
        obj["Key"]
        for obj in response.get("Contents", [])
    ]


def run_backfill():
    """Replay all raw staged AQI objects through the transformation pipeline.

    The function logs progress per file, skips missing objects safely, and
    continues processing the remainder of the backfill even if one file raises
    an application-level error.
    """

    raw_files = list_raw_files()

    logger.info(
        f"Found {len(raw_files)} files"
    )

    for key in raw_files:

        try:
            logger.info(
                f"Backfilling {key}"
            )

            save_transformed_data_to_bucket(
                key
            )

        except KeyError:
            logger.warning(
                f"{key} not found. Skipping..."
            )

            continue

        except Exception as e:
            logger.error(
                f"Failed to process {key}: {e}"
            )

            send_telegram_alert(
                f"Failed to process {key}: {e}"
            )

            continue

    logger.info(
        "Backfill completed"
    )


run_backfill()