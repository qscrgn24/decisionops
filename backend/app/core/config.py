from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIB = 1024 * 1024
_MULTIPART_OVERHEAD_ALLOWANCE = 64 * 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "DecisionOps"
    ENV: str = "production"
    DATABASE_URL: str = ""
    DO_SESSION_SECRET: str = ""

    # Request and dataset boundaries
    MAX_REQUEST_BYTES: int = Field(
        default=3 * _MIB,
        ge=128 * 1024,
        le=100 * _MIB,
    )
    MAX_UPLOAD_BYTES: int = Field(
        default=2 * _MIB,
        ge=1024,
        le=50 * _MIB,
    )
    MAX_DATASET_ROWS: int = Field(
        default=5_000,
        ge=1,
        le=1_000_000,
    )
    MAX_DATASET_COLUMNS: int = Field(
        default=50,
        ge=1,
        le=1_000,
    )
    MAX_CELL_CHARS: int = Field(
        default=2_000,
        ge=1,
        le=1_000_000,
    )
    MAX_DATASET_NAME_CHARS: int = Field(
        default=100,
        ge=1,
        le=255,
    )
    MAX_FILENAME_CHARS: int = Field(
        default=255,
        ge=1,
        le=300,
    )

    @model_validator(mode="after")
    def validate_upload_limits(self) -> Self:
        minimum_request_size = (
            self.MAX_UPLOAD_BYTES + _MULTIPART_OVERHEAD_ALLOWANCE
        )

        if self.MAX_REQUEST_BYTES < minimum_request_size:
            raise ValueError(
                "MAX_REQUEST_BYTES must exceed MAX_UPLOAD_BYTES by at "
                "least 65536 bytes for multipart request overhead."
            )
        
        return self



settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")
if not settings.DO_SESSION_SECRET:
    raise RuntimeError("DO_SESSION_SECRET is required")