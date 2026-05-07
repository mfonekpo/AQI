from airflow.sdk import dag, task

from etl.ingest import ingest_to_bucket
import pendulum


@task(retries=3)
def ingestion():
    ingest_to_bucket()


@dag(
    schedule="@hourly",
    # schedule="* * * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
)
def taskflow():
    ingestion()


taskflow()
