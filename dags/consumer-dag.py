from airflow.sdk import dag, task, Context
from alerting.alert import send_telegram_alert
from etl.consume import receive_sqs_message, delete_message
from utils.logging_conf import logger
import pendulum
from etl.sensors import ingestion_sensor_decorator
from etl.transform import save_transformed_data_to_bucket


def on_failure_callback(context: Context) -> None:
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
    message = receive_sqs_message()
    if not message:
        return
    try:
        save_transformed_data_to_bucket(message["s3_key"])
        delete_message(message["receipt_handle"])
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

    # define ingestion sensor task
    wait_for_data = ingestion_sensor_decorator()

    wait_for_data >> process_sqs_message()


# Instantiate the DAG
dag_run()