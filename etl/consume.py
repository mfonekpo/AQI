import json
from urllib.parse import unquote
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
import os
from utils.aws_conf import create_sqs_client
from dotenv import load_dotenv
from dataclasses import dataclass
from pydantic import ValidationError
from etl.validate import SqsSensorMessage, S3EventBody


load_dotenv()


EXPECTED_BUCKET = "aqi-staging"
EXPECTED_PREFIX = "raw_data/"
EXPECTED_SUFFIX = ".json"
S3_TEST_EVENT = "s3:TestEvent"
OBJECT_CREATED_PREFIX = "ObjectCreated:"


@dataclass
class ParsedS3Event:
    message_id: str
    receipt_handle: str
    bucket: str
    key: str
    event_name: str
    e_tag: str | None = None
    version_id: str | None = None

def parse_s3_event_message(message: dict) -> ParsedS3Event | None:
    """
    Validates and filters an SQS message containing an S3 event.

    Returns ParsedS3Event for processable raw AQI objects, None for known
    irrelevant events, and raises ValueError for malformed messages.
    """
    try:
        sqs_message = SqsSensorMessage.model_validate(message)
        message_body = json.loads(sqs_message.body)
    except (ValidationError, json.JSONDecodeError) as e:
        raise ValueError(f"Invalid SQS message shape: {e}") from e

    if not isinstance(message_body, dict):
        raise ValueError(f"SQS message Body must decode to a JSON object: {message_body}")

    if message_body.get("Event") == S3_TEST_EVENT:
        logger.info("Skipping S3 test event")
        return None

    try:
        s3_event = S3EventBody.model_validate(message_body)
    except ValidationError as e:
        raise ValueError(f"Invalid S3 event body: {e}") from e

    record = s3_event.records[0]
    event_name = record.event_name

    if not event_name.startswith(OBJECT_CREATED_PREFIX):
        logger.info(f"Skipping non-ObjectCreated event: {event_name}")
        return None

    bucket = record.s3.bucket.name
    s3_object = record.s3.s3_object
    key = unquote(s3_object.key)

    if bucket != EXPECTED_BUCKET:
        logger.info(f"Skipping event from unexpected bucket: {bucket}")
        return None

    if not key.startswith(EXPECTED_PREFIX) or not key.endswith(EXPECTED_SUFFIX):
        logger.info(f"Skipping event for unsupported key: {key}")
        return None

    return ParsedS3Event(
        message_id=sqs_message.message_id,
        receipt_handle=sqs_message.receipt_handle,
        bucket=bucket,
        key=key,
        event_name=event_name,
        e_tag=s3_object.e_tag,
        version_id=s3_object.version_id
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
