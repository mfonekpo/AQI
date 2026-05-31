from alerting.alert import send_telegram_alert
from utils.logging_conf import logger
from airflow.sdk import get_current_context
from urllib.parse import unquote
from datetime import datetime, timezone
from utils.time_utils import now_wat
import json

from utils.supabase_conf import create_s3_client


def get_loaded_file_key_from_bucket():
    context = get_current_context()
    messages = context["ti"].xcom_pull(
        task_ids="watch_data_staging",
        key="messages"
    )

    message_body = json.loads(messages[0]["Body"])
    message_key = unquote((message_body.get("Records")[0].get("s3").get("object").get("key")))

    return message_key


def get_data_from_bucket(key: str) -> dict:
    """
    Fetches a JSON object from the S3 bucket given its key.
    """

    bucket_name = "aqi-staging"
    s3_client = create_s3_client()

    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=key)
        data = response["Body"].read().decode("utf-8")
        return json.loads(data)
    except Exception as e:
        logger.error(f"Failed to fetch data from bucket: {e}")
        send_telegram_alert(f"Failed to fetch data from bucket: {e}")
        raise


def convert_date_from_unix_to_datetime():
    """
    Transformation layer — only responsibility is transforming the data.
    Has zero knowledge of HTTP, validation, or storage.
    Receives already-validated data as a plain dict and returns a transformed dict.
    """

    key = get_loaded_file_key_from_bucket()
    data = get_data_from_bucket(key)

    date_value = datetime.fromtimestamp(data["date"], tz=timezone.utc)

    logger.info("Data transformation logic fired")
    send_telegram_alert("Data transformation logic fired")

    return {
        "aqi": data["aqi"],
        "date": date_value.strftime("%Y-%m-%d %H:%M:%S"),
        "co_value": data["co_value"],
        "ozone_value": data["ozone_value"]
    }


def save_transformed_data_to_bucket():
    """
    Orchestration layer — only responsibility is orchestrating the transformation
    and storage layers. Has zero knowledge of the inner workings of either layer.
    """

    transformed_data = convert_date_from_unix_to_datetime()

    bucket_name = "aqi-transform"
    s3_client = create_s3_client()
    now = datetime.now(timezone.utc)
    key = f"transformed_data/year={now.year}/month={now.month:02d}/day={now.day:02d}/hour={now.hour:02d}/aqi.json"

    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json.dumps(transformed_data),
        )
        logger.info(f"Data successfully ingested to {bucket_name}: {key}")
        logger.info(f"Data saved at {now_wat().strftime("%Y-%m-%d %H:%M:%S %Z")}")
        send_telegram_alert(f"Data successfully ingested to {bucket_name}: {key}")
        send_telegram_alert(f"Data saved at {now_wat().strftime("%Y-%m-%d %H:%M:%S %Z")}")
    except Exception as e:
        logger.error(f"Failed to ingest data to {bucket_name}: {e}")
        send_telegram_alert(f"Failed to ingest data to {bucket_name}: {e}")
        raise