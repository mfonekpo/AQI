"""Airflow consumer DAG for processing staged AQI S3 events from SQS.

The consumer pipeline waits for raw S3 object creation notifications, reads
 the queued message contents, transforms the referenced object into a
Parquet-ready record, and removes the original SQS message after successful
processing.
"""

from airflow.sdk import dag, task, Context, get_current_context
from alerting.alert import send_telegram_alert
from etl.consume import parse_s3_event_message, delete_message
from utils.logging_conf import logger
import pendulum
from etl.sensors import ingestion_sensor_decorator
from etl.transform import save_transformed_data_to_bucket


def on_failure_callback(context: Context) -> None:
    """Send an operational alert when the consumer DAG task fails.

    Args:
        context: Airflow task context containing DAG, task instance, and run
            metadata used to build the failure message.
    """
    dag_id  = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id  = context["run_id"]
    send_telegram_alert(
        f"❌ Pipeline failed!\n"
        f"DAG:  {dag_id}\n"
        f"Task: {task_id}\n"
        f"Run:  {run_id}"
    )

@task()
def process_sqs_message():
    """Process the first queued S3 event message for the AQI pipeline.

    The function retrieves the most recent sensor message through XCom, parses
    the S3 event envelope, writes the transformed artifact to the transformed
    object store, and deletes the corresponding SQS message if processing
    succeeds.
    """

    context = get_current_context()

    messages = context["ti"].xcom_pull(
        task_ids="ingestion_SQS_sensor",
        key="messages"
    )

    if not messages:
        logger.warning("No messages in XCom")
        send_telegram_alert("No messages in XCom for sensor log task")
        return
    message = messages[0]
    parsed_event = parse_s3_event_message(message)

    if parsed_event is None:
        delete_message(message["ReceiptHandle"])
        return
    try:
        logger.info(f"Processing S3 object: {parsed_event.bucket}/{parsed_event.key}")

        save_transformed_data_to_bucket(parsed_event.key)

        delete_message(parsed_event.receipt_handle)

        logger.info(f"Successfully processed message: {parsed_event.message_id}")

    except Exception as e:
        logger.error(f"Failed to process SQS message: {e}")
        send_telegram_alert(f"Failed to process SQS message: {e}")
        raise


@dag(
    dag_id = "aqi_consumer_dag",
    schedule="@continuous",
    start_date=pendulum.datetime(2026, 5, 28, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    on_failure_callback=on_failure_callback,
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(seconds=120)
    },
)

def dag_run():
    """Define the DAG graph for the consumer pipeline.

    Returns:
        None. The DAG structure is created by wiring the ingestion sensor to
        the message-processing task.
    """

    # define ingestion sensor task
    wait_for_data = ingestion_sensor_decorator()

    wait_for_data >> process_sqs_message()


# Instantiate the DAG
dag_run()