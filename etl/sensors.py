from airflow.providers.amazon.aws.sensors.sqs import SqsSensor

def ingestion_sensor_decorator():
    """
    Returns a configured SqsSensor.
    Must be called at DAG level.
    """
    return SqsSensor(
        task_id="ingestion_SQS_sensor",
        sqs_queue="https://sqs.us-east-1.amazonaws.com/158449849022/aqi-sensor-queue",
        max_messages=1,
        num_batches=1,
        region_name="us-east-1",
        wait_time_seconds=20,         # Long polling
        poke_interval=60,           # Check every minute
        timeout=5400,                 # Fail after 1hr:30mins
        mode="reschedule",            # Free up worker slot between pokes
        delete_message_on_reception=False,  # Prevent duplicate processing
        aws_conn_id="aws_default"
    )

def transformation_sensor_decorator():
    return SqsSensor(
        task_id = "transformation_SQS_sensor",
        sqs_queue="https://sqs.us-east-1.amazonaws.com/158449849022/aqi-transform-queue",
        max_messages = 10,
        num_batches = 1,
        region_name = "us-east-1",
        wait_time_seconds = 20,
        poke_interval = 60,
        timeout = 4000,
        mode = "reschedule",
        delete_message_on_reception = True,
        aws_conn_id = "aws_default"
    )
