from alerting.alert import send_telegram_alert
from utils.logging_conf import logger
import json
from airflow.sdk import get_current_context
from urllib.parse import unquote




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
