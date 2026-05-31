from airflow.providers.amazon.aws.sensors.sqs import SqsSensor
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
from airflow.sdk import get_current_context
from urllib.parse import unquote
import json


def ingestion_sensor_decorator():
    """
    Returns a configured SqsSensor.
    Must be called at DAG level.
    """
    return SqsSensor(
        task_id="watch_data_staging",
        sqs_queue="https://sqs.us-east-1.amazonaws.com/158449849022/aqi-sensor-queue",
        max_messages=10,
        num_batches=1,
        region_name="us-east-1",
        wait_time_seconds=20,         # Long polling
        poke_interval=3600,           # Check every 1 hr
        timeout=4000,                 # Fail after ~1hr 6mins
        mode="reschedule",            # Free up worker slot between pokes
        delete_message_on_reception=True,  # Prevent duplicate processing
        aws_conn_id="aws_default"
    )


def transformation_sensor_decorator():
    return SqsSensor(
        task_id = "watch_data_transformation",
        sqs_queue="https://sqs.us-east-1.amazonaws.com/158449849022/aqi-transform-queue",
        max_messages = 10,
        num_batches = 1,
        region_name = "us-east-1",
        wait_time_seconds = 20,
        poke_interval = 3600,
        timeout = 4000,
        mode = "reschedule",
        delete_message_on_reception = True,
        aws_conn_id = "aws_default"
    )


def log_file_detected(task_id: str):
    """Call this AFTER sensor succeeds — reads key from SQS message via XCom."""
    context  = get_current_context()
    messages = context["ti"].xcom_pull(
        task_ids=task_id,
        key="messages"
    )

    if not messages:
        logger.warning("No messages in XCom")
        send_telegram_alert("No messages in XCom for sensor log task")
        return

    message_body = json.loads(messages[0]["Body"])
    records      = message_body.get("Records")

    # Guard against S3 test event which has no Records
    if not records:
        logger.info("S3 test event received — skipping")
        return

    # Safe to access now — records is guaranteed to exist
    message_key = unquote(records[0]["s3"]["object"]["key"])

    send_telegram_alert(f"New file detected: {message_key}")
    logger.info(f"New file detected: {message_key}")