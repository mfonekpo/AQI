from airflow.sdk import dag, task

from etl.ingest import ingest_to_bucket
import pendulum

@task(retries=3)
def ingestion():
    ingest_to_bucket()


@dag(
    # schedule="@hourly",
    schedule="* * * * *",
    start_date=pendulum.now(tz="UTC").subtract(days=1),
    catchup=False,
    is_paused_upon_creation=False,
)
def taskflow():
    ingestion()


taskflow()