# AQI Batch Pipeline

A production-ready Air Quality Index (AQI) batch pipeline for ingestion, validation, transformation, and persistence using Apache Airflow, AWS S3/SQS, and Telegram alerting.

## Overview

This project implements a two-stage data pipeline:

- **Producer DAG**: fetches air quality data from OpenWeatherMap and writes raw JSON to an S3 staging bucket.
- **Consumer DAG**: listens for SQS notifications from S3, transforms the raw data into parquet format, writes Parquet to a transformed S3 bucket, and loads the transformed data into Snowflake.

The pipeline is designed for fault tolerance and operational visibility, with retries, logging, and Telegram alert notifications for failures.

## Architecture

- `dags/producer-dag.py`

  - Runs hourly
  - Executes `etl.ingest.ingest_to_bucket()`
  - Saves validated raw readings to `aqi-staging`
- `dags/consumer-dag.py`

  - Runs continuously using an SQS sensor
  - Reads S3 event notifications from `aqi-sensor-queue`
  - Validates and transforms raw data, then writes parquet output to `aqi-transform`
- `etl/`

  - `fetch.py`: API integration and raw reading validation
  - `ingest.py`: ingestion orchestration and staging bucket persistence
  - `consume.py`: SQS event parsing and message deletion
  - `transform.py`: S3 retrieval, data transformation, parquet conversion, and transformed bucket persistence
  - `validate.py`: shared pydantic models and data validation logic
  - `sensors.py`: Airflow SQS sensor definitions
  - `storage.py`: bucket retrieval and raw storage helpers
- `alerting/`

  - Telegram alert integration for failures and operational notifications
- `utils/`

  - AWS client creation
  - logging configuration
  - timezone helper utilities

## Features

- Airflow-based orchestration with Celery worker model
- S3 staging and transform storage
- SQS sensor-driven event processing
- Structured validation using Pydantic
- Parquet output for transformed AQI data
- Telegram alerting for failed pipeline runs
- Modular ETL layers with clear separation of concerns

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local dependency installation and linting)
- AWS credentials with S3 and SQS permissions
- Telegram bot token and chat ID
- OpenWeatherMap API key

## Environment Variables

Create a `.env` file in the project root with the following values:

```env
WEATHERAPI=<openweathermap_api_key>
LAT=<latitude>
LONG=<longitude>
access_key=<aws_access_key_id>
secret_access_key=<aws_secret_access_key>
region=<aws_region>
TELEGRAM_TOKEN=<telegram_bot_token>
TELEGRAM_CHAT_ID=<telegram_chat_id>
STAGING_QUEUE_URL=<sqs_staging_queue_url>
```

> Note: The code also uses `aws_default` as the Airflow AWS connection ID for sensor execution. Configure this connection in Airflow or set AWS credential environment variables in the container runtime.

## Infrastructure

The pipeline expects the following infrastructure:

- S3 bucket: `aqi-staging`
- S3 bucket: `aqi-transform`
- SQS queue: `https://sqs.us-east-1.amazonaws.com/158449849022/aqi-sensor-queue`
- Snowflake database and warehouse with an external stage loading from `aqi-transform/transformed_data/`
- Optional SQS queue: `aqi-transform-queue` (defined in `etl/sensors.py` but not currently used by the main DAGs)

Terraform resources are defined under `my-infra/`, including Snowflake database, warehouse, stage, file format, and pipe configuration.

## Setup

1. Clone the repository and switch to the project root:

```bash
cd /home/royale/Documents/code_files/personal_project/batch/AQI
```

2. Install Python dependencies locally (optional, for linting and local script execution):

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

3. Configure `.env` with AWS, Telegram, and OpenWeatherMap credentials.

## Running Locally with Docker Compose

This repository includes a Docker Compose stack for Airflow:

```bash
docker compose up --build
```

The Airflow API server is exposed on:

- `http://localhost:8080`

The stack includes:

- `postgres` for metadata
- `redis` for Celery broker
- `airflow-apiserver`
- `airflow-scheduler`
- `airflow-dag-processor`
- `airflow-worker`
- `airflow-triggerer`
- `airflow-init`
- `airflow-cli`

### Airflow CLI Example

To list DAGs:

```bash
docker compose exec airflow-cli airflow dags list
```

To trigger a DAG manually:

```bash
docker compose exec airflow-cli airflow dags trigger aqi_producer_dag
docker compose exec airflow-cli airflow dags trigger aqi_consumer_dag
```

## DAGs

### `aqi_producer_dag`

- Schedule: `@hourly`
- Starts fetching AQI data from OpenWeatherMap
- Writes validated raw JSON to the staging bucket
- Retries: 2 times with 120-second delay

### `aqi_consumer_dag`

- Schedule: `@continuous`
- Uses `SqsSensor` to poll the staging queue
- Processes the first message from XCom
- Converts raw event data to parquet and writes to transform bucket
- Deletes the SQS message after successful processing

## Logging and Monitoring

- Runtime logs are stored in `logs/pipeline.log`
- Monitoring errors are written to `logs/monitoring.log`
- Airflow task failures send Telegram alerts via `alerting.alert.send_telegram_alert()`

## Extending the Pipeline

Recommended extension points:

- Add unit tests for `etl/fetch.py`, `etl/transform.py`, and `etl/consume.py`
- Add a dedicated Airflow connection for AWS credentials instead of relying on environment variables
- Add production-grade secret management for `.env` values
- Add data quality checks or a Great Expectations validation step before transformation
- Add a downstream loader DAG to ingest transformed parquet data into a warehouse or analytics store

## Notes

- `config/airflow.cfg` is included for Airflow configuration, but the project currently uses Docker Compose environment overrides.
- `pyproject.toml` only contains mypy configuration.
- The project is designed for a batch/event-driven ETL workflow with clear separation between ingestion, validation, transformation, storage, and alerting.

## License

This repository does not currently define a license file. Add a `LICENSE` if you want to make the repository open source.
