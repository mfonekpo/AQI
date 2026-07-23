"""Consumer utilities for decoding AWS SQS/S3 notification events.

This module parses SQS messages produced by S3 object-created notifications,
filters out unsupported or test events, and exposes a small, typed domain
object for later transformation work.
"""

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
    """Typed representation of a supported S3 object-created SQS notification.

    Attributes:
        message_id: The unique SQS message identifier.
        receipt_handle: The handle used to delete the message after processing.
        bucket: The originating S3 bucket name.
        key: The fully decoded object key.
        event_name: The AWS event name extracted from the S3 notification.
        e_tag: Optional ETag metadata for the object.
        version_id: Optional S3 version identifier.
    """
    message_id: str
    receipt_handle: str
    bucket: str
    key: str
    event_name: str
    e_tag: str | None = None
    version_id: str | None = None

def parse_s3_event_message(message: dict) -> ParsedS3Event | None:
    """Validate and normalize a raw SQS message into a processable S3 event.

    Args:
        message: A raw dictionary payload representing the SQS message.

    Returns:
        A ``ParsedS3Event`` instance when the message represents a supported
        raw AQI object creation event; otherwise ``None`` for benign filtered
        events such as S3 test notifications or unsupported bucket prefixes.

    Raises:
        ValueError: If the message shape is malformed or the embedded S3 event
            envelope cannot be validated.
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
    """Validate that an SQS queue URL is configured for the current runtime.

    Args:
        queue_url: The queue URL from the environment or a caller-provided value.

    Returns:
        The validated queue URL string.

    Raises:
        ValueError: If no queue URL is configured.
    """
    if not queue_url:
        error_msg = "STAGING_QUEUE_URL environment variable is not set."
        logger.error(error_msg)
        send_telegram_alert(error_msg)
        raise ValueError(error_msg)
    return queue_url

def delete_message(receipt_handle: str, queue_url: str | None = None) -> None:
    """Delete an SQS message using its receipt handle.

    Args:
        receipt_handle: The SQS message receipt handle that authorizes deletion.
        queue_url: Optional queue URL override. When omitted, the function
            resolves the value from the ``STAGING_QUEUE_URL`` environment
            variable.

    Raises:
        Exception: If the SQS delete operation fails.
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
