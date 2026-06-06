from airflow.sdk import dag, task
from airflow.task.trigger_rule import TriggerRule
from alerting.alert import send_telegram_alert
from etl.ingest import ingest_to_bucket
from etl.sensors import ingestion_sensor_decorator, transformation_sensor_decorator
from etl.transform import save_transformed_data_to_bucket
from alerting.sensor_logging import log_file_detected
import pendulum


def on_failure_callback(context: dict) -> None:
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


# Call the ingestion sensor at DAG level
wait_for_new_data = ingestion_sensor_decorator()

# Call the transformation sensor at DAG level
wait_for_transformed_data = transformation_sensor_decorator()


# Sensor logging for staging
@task(trigger_rule=TriggerRule.ALL_SUCCESS)
def log_sensor_success():
    log_file_detected(task_id="ingestion_SQS_sensor")


# Sensor logging for transformation
@task(trigger_rule=TriggerRule.ALL_SUCCESS)
def log_transformation_success():
    log_file_detected(task_id="transformation_SQS_sensor")


@task()
def transformation():
    save_transformed_data_to_bucket()


@dag(
    dag_id="aqi_data_pipeline",
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 5, 28, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=3,
    on_failure_callback=on_failure_callback
)

def taskflow():
    ingest    = ingestion()
    ingestion_sensor    = wait_for_new_data
    transformation_sensor = wait_for_transformed_data
    transform = transformation()
    sensor_log_staging       = log_sensor_success()
    sensor_log_transform = log_transformation_success()

    # ✅ Critical path — logging is completely removed
    ingest >> ingestion_sensor >> transform >> transformation_sensor

    # ✅ Logging runs in parallel after sensor — doesn't block transformation
    ingestion_sensor >> sensor_log_staging
    transformation_sensor >> sensor_log_transform

# Instantiate the DAG
taskflow()
