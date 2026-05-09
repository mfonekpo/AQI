from pydantic import BaseModel, field_validator

class AirqualityFetchError(Exception):
    """
    Raised when any part of the air quality pipeline fails.
    Defined here so all layers can import it without circular imports.
    """
    pass


class AirQualityReading(BaseModel):
    """
    Validation layer — only responsibility is validating the shape
    and business rules of a single air quality reading.
    Has zero knowledge of HTTP, storage, or alerting.
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