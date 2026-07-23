"""Airflow producer DAG for publishing raw AQI readings to the staging S3 bucket.

This DAG is responsible for the ingestion stage of the AQI data pipeline.
It runs on an hourly schedule and delegates the actual fetch-and-store work
via the reusable ingestion orchestration function.
"""

from airflow.sdk import dag, task, Context
from alerting.alert import send_telegram_alert
from etl.ingest import ingest_to_bucket
import pendulum


def on_failure_callback(context: Context) -> None:
    """Send an operational alert when the producer DAG task fails.

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
def ingestion():
    """Execute the ingest orchestration step for a single DAG run.

    Returns:
        None. The function triggers the write into the staging S3 bucket and
        relies on the underlying ingestion layer for error handling.
    """
    ingest_to_bucket()

@dag(
    dag_id="aqi_producer_dag",
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 5, 28, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=3,
    on_failure_callback=on_failure_callback,
    default_args={
        "retries": 2,
        "retry_delay": pendulum.duration(seconds=120)
    },
)

def producer_dag_run():
    """Create and configure the producer DAG definition.

    Returns:
        None. The DAG object is instantiated when the module is imported.
    """
    ingestion()


# Instantiate the DAG
producer_dag_run()
