from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
from airflow.sdk import get_current_context


def sensor_decorator():
    """
    Returns a configured S3KeySensor.
    Must be called at DAG level.
    """

    return S3KeySensor(
        task_id="watch_data_staging",
        bucket_name = "aqi-staging",
        # bucket_key = "raw_data/year=*/month=*/day=*/hour=*/aqi.json",
        bucket_key = (
            "raw_data/"
            "year={{ logical_date.strftime('%Y') }}/"
            "month={{ logical_date.strftime('%m') }}/"
            "day={{ logical_date.strftime('%d') }}/"
            "hour={{ logical_date.strftime('%H') }}/"
            "aqi.json"
        ),
        poke_interval=3600,   # check every 1 hr
        timeout=4000,         # fail after 1hr:60mins
        mode="reschedule",    # free up worker slot when the sensor is not poking
        aws_conn_id="aws_default"
    )


def log_file_detected():
    """Call this AFTER sensor succeeds — logs and alerts accurately."""
    context = get_current_context()
    date_context = context["data_interval_end"]

    key = (
        f"raw_data/"
        f"year={date_context.strftime('%Y')}/"
        f"month={date_context.strftime('%m')}/"
        f"day={date_context.strftime('%d')}/"
        f"hour={date_context.strftime('%H')}/"
        f"aqi.json"
    )

    logger.info(f"File detected in staging bucket: {key}")
    send_telegram_alert(f"File detected in staging bucket: {key}")