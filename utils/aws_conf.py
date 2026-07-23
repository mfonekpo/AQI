"""Shared AWS client factories for S3 and SQS access.

The module centralizes credential lookup and boto3 session creation so the
rest of the pipeline can reuse a consistent configuration surface.
"""

from utils.logging_conf import logger
import boto3
import os
from dotenv import load_dotenv

load_dotenv()


def create_s3_client():
    """Create a configured boto3 S3 client for the current environment.

    Returns:
        A boto3 S3 client instance that can be used to interact with the
        configured bucket namespace.
    """
    try:
        access_key = os.getenv("access_key")
        secret_key = os.getenv("secret_access_key")
        region = os.getenv("region")


        session = boto3.session.Session()

        s3_client = session.client(
            service_name="s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        logger.info("S3 client created successfully")
        return s3_client
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}")
        raise


def create_sqs_client():
    """Create a configured boto3 SQS client for the current environment.

    Returns:
        A boto3 SQS client instance that can be used to interact with the
        configured queue namespace.
    """
    try:
        access_key = os.getenv("access_key")
        secret_key = os.getenv("secret_access_key")
        region = os.getenv("region")

        session = boto3.session.Session()

        sqs_client = session.client(
            service_name="sqs",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        logger.info("SQS client created successfully")
        return sqs_client
    except Exception as e:
        logger.error(f"Failed to create SQS client: {e}")
        raise