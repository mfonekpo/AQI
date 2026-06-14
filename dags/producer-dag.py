from airflow.sdk import dag, task, Context
from alerting.alert import send_telegram_alert
from etl.ingest import ingest_to_bucket
import pendulum


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
def ingestion():
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
    ingestion()


# Instantiate the DAG
producer_dag_run()
