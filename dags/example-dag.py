from airflow.sdk import dag, task
from airflow.utils.trigger_rule import TriggerRule
from etl.ingest import ingest_to_bucket
from etl.sensors import sensor_decorator, log_file_detected
from etl.transform import save_transformed_data_to_bucket
import pendulum



@task()
def ingestion():
    ingest_to_bucket()


# Call the sensor at DAG level
wait_for_new_data = sensor_decorator()


@task(trigger_rule=TriggerRule.ALL_DONE)
def log_sensor_success():
    log_file_detected()


@task()
def transformation():
    save_transformed_data_to_bucket()


@dag(
    schedule="@hourly",
    start_date=pendulum.datetime(2026, 1, 1, tz="Africa/Lagos"),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=3,
)

def taskflow():
    ingest    = ingestion()
    sensor    = wait_for_new_data
    transform = transformation()
    log       = log_sensor_success()

    # ✅ Critical path — logging is completely removed
    ingest >> sensor >> transform

    # ✅ Logging runs in parallel after sensor — doesn't block transformation
    sensor >> log

# Instantiate the DAG
taskflow()
