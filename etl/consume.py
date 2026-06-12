import boto3
import json
from urllib.parse import unquote
from utils.logging_conf import logger
from alerting.alert import send_telegram_alert
import os
from dotenv import load_dotenv


load_dotenv()

def validate_queue_url(queue_url: str | None) -> str:
    if not queue_url:
        error_msg = "STAGING_QUEUE_URL environment variable is not set."
        logger.error(error_msg)
        send_telegram_alert(error_msg)
        raise ValueError(error_msg)
    return queue_url

def receive_sqs_message(queue_url: str | None = None) -> dict | None:
    """
    Reads one message from SQS.

    Returns:
        {
            "receipt_handle": str,
            "s3_key": str
        }

    or None if queue empty.
    """

    sqs_client = boto3.client("sqs", region_name="us-east-1")
    queue_url = queue_url or validate_queue_url(
        os.getenv("STAGING_QUEUE_URL")
    )

    try:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=120
        )
        messages = response.get("Messages", [])

        if not messages:
            logger.info("No messages in SQS queue.")
            return None

        message_body = json.loads(messages[0]["Body"])

        records = message_body.get("Records", [])

        if not records:
            logger.warning("Received SQS message without 'Records' field.")
            raise ValueError("Received SQS message without 'Records' field.")

        record = records[0]

        s3_key = unquote(record["s3"]["object"]["key"])
        receipt_handle = messages[0]["ReceiptHandle"]
        if not receipt_handle:
            logger.warning("Received SQS message without 'ReceiptHandle'.")
            raise ValueError("Received SQS message without 'ReceiptHandle'.")

        return {
            "receipt_handle": receipt_handle,
            "s3_key": s3_key
        }
    except Exception as e:
        logger.error(f"Failed to receive SQS message: {e}")
        send_telegram_alert(f"Failed to receive SQS message: {e}")
        raise

def delete_message(receipt_handle: str, queue_url: str | None = None) -> None:
    """
    Deletes a message from SQS using its receipt handle.
    """
    sqs_client = boto3.client("sqs", region_name="us-east-1")
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