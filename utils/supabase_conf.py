from utils.logging_conf import logger
import boto3
import os
from dotenv import load_dotenv

load_dotenv()


def create_s3_client():
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
        return None
