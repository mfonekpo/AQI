"""Pydantic validation models and shared domain errors for the AQI pipeline.

The schemas in this module define the contract boundaries for raw AQI fetches,
transformed analytics records, and the S3/SQS event envelope consumed by the
consumer DAG.
"""

from datetime import datetime
from pydantic import BaseModel, field_validator, Field, ConfigDict

class AirqualityFetchError(Exception):
    """Raised when the AQI fetch or validation path fails unexpectedly.

    This exception is intentionally shared across layers so the ingestion and
    processing pipeline can report a single domain-level failure mode.
    """
    pass


class AirQualityReading(BaseModel):
    """Validate the structure of a single raw AQI reading payload.

    The model guarantees that the API response shape is normalized sufficiently
    for downstream storage and transformation operations.
    """
    aqi: int
    date: int
    co_value: float
    ozone_value: float

    @field_validator("aqi")
    @classmethod
    def aqi_must_be_in_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError(f"AQI value {v} is outside expected range 1-5")
        return v


class AirQualityTransformedReading(BaseModel):
    """Validate the schema of a transformed AQI analytics record.

    This model ensures that the fully normalized record is suitable for Parquet
    serialization and downstream warehouse ingestion.
    """
    aqi: int
    date_epoch: int
    date_utc: datetime
    co_value: float
    ozone_value: float

    @field_validator("aqi")
    @classmethod
    def aqi_must_be_in_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError(f"AQI value {v} is outside expected range 1-5")
        return v
    

class AwsEventModel(BaseModel):
    """Base model for AWS event payloads with permissive alias handling.

    The configuration ignores unknown fields and supports alias-based input
    mapping for AWS event envelopes.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class SqsSensorMessage(AwsEventModel):
    message_id: str = Field(alias="MessageId")
    receipt_handle: str = Field(alias="ReceiptHandle")
    body: str = Field(alias="Body")


class S3Bucket(AwsEventModel):
    name: str


class S3Object(AwsEventModel):
    key: str
    e_tag: str | None = Field(default=None, alias="eTag")
    version_id: str | None = Field(default=None, alias="versionId")


class S3Entity(AwsEventModel):
    bucket: S3Bucket
    s3_object: S3Object = Field(alias="object")


class S3EventRecord(AwsEventModel):
    event_name: str = Field(alias="eventName")
    s3: S3Entity


class S3EventBody(AwsEventModel):
    records: list[S3EventRecord] = Field(alias="Records")

    @field_validator("records")
    @classmethod
    def records_must_not_be_empty(cls, value):
        if not value:
            raise ValueError("S3 event body must contain at least one record")
        return value