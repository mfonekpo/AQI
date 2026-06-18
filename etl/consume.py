import json
from urllib.parse import unquote
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
import os
from utils.aws_conf import create_sqs_client
from dotenv import load_dotenv
from dataclasses import dataclass


load_dotenv()


@dataclass
class ParsedS3Event:
    message_id: str
    receipt_handle: str
    bucket: str
    key: str
    event_name: str

def parse_s3_event_message(message: dict) -> ParsedS3Event | None:
    message_body = json.loads(message["Body"])

    if message_body.get("Event") == "s3:TestEvent":
        logger.info("Skipping S3 test event")
        return None
    records = message_body.get("Records", [])

    if not records:
        raise ValueError(f"Unexpected SQS message body: {message_body}")

    record = records[0]
    event_name = record.get("eventName", "")

    if not event_name.startswith("ObjectCreated:"):
        logger.info(f"Skipping non-ObjectCreated event: {event_name}")
        return None
    
    bucket = record["s3"]["bucket"]["name"]
    key = unquote(record["s3"]["object"]["key"])
    if bucket != "aqi-staging":
        logger.info(f"Skipping event from unexpected bucket: {bucket}")
        return None

    if not key.startswith("raw_data/") or not key.endswith(".json"):
            logger.info(f"Skipping event for unsupported key: {key}")
            return None

    return ParsedS3Event(
        message_id=message["MessageId"],
        receipt_handle=message["ReceiptHandle"],
        bucket=bucket,
        key=key,
        event_name=event_name
    )

def validate_queue_url(queue_url: str | None) -> str:
    if not queue_url:
        error_msg = "STAGING_QUEUE_URL environment variable is not set."
        logger.error(error_msg)
        send_telegram_alert(error_msg)
        raise ValueError(error_msg)
    return queue_url

def delete_message(receipt_handle: str, queue_url: str | None = None) -> None:
    """
    Deletes a message from SQS using its receipt handle.
    """
    sqs_client = create_sqs_client()
    queue_url = queue_url or validate_queue_url(
        os.getenv("STAGING_QUEUE_URL")
    )

    try:
        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        logger.info("SQS message deleted.")
    except Exception as e:
        logger.error(f"Failed to delete SQS message: {e}")
        send_telegram_alert(f"Failed to delete SQS message: {e}")
        raise