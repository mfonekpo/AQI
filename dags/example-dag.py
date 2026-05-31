from airflow.sdk import dag, task
from airflow.task.trigger_rule import TriggerRule
from etl.ingest import ingest_to_bucket
from etl.sensors import ingestion_sensor_decorator, transformation_sensor_decorator, log_file_detected
from etl.transform import save_transformed_data_to_bucket
import pendulum


@task()
def ingestion():
    ingest_to_bucket()


# Call the ingestion sensor at DAG level
wait_for_new_data = ingestion_sensor_decorator()

# Call the transformation sensor at DAG level
wait_for_transformed_data = transformation_sensor_decorator()


# Sensor logging for staging
@task(trigger_rule=TriggerRule.ALL_DONE)
def log_sensor_success():
    log_file_detected(task_id="watch_data_staging")

# Sensor logging for transformation
@task(trigger_rule=TriggerRule.ALL_DONE)
def log_transformation_success():
    log_file_detected(task_id="watch_data_transformation")


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
