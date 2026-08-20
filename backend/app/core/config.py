from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_MIB = 1024 * 1024
_MULTIPART_OVERHEAD_ALLOWANCE = 64 * 1024
_MIN_SESSION_SECRET_CHARS = 32

_PRODUCTION_ENVS = {
    "production",
    "prod",
    "production_debug",
}

_UNSAFE_PRODUCTION_SESSION_SECRETS = {
    "your-secret-key-here-longer-than-32-characters",
    "test-secret-do-not-use-in-production",
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "DecisionOps"
    ENV: str = "production"
    DATABASE_URL: str = ""
    DO_SESSION_SECRET: str = ""

    # Request and dataset boundaries
    MAX_REQUEST_BYTES: int = Field(default=3 * _MIB, ge=128 * 1024, le=100 * _MIB)
    MAX_UPLOAD_BYTES: int = Field(default=2 * _MIB, ge=1024, le=50 * _MIB)
    MAX_DATASET_ROWS: int = Field(default=5_000, ge=1, le=1_000_000)
    MAX_DATASET_COLUMNS: int = Field(default=50, ge=1, le=1_000)
    MAX_CELL_CHARS: int = Field(default=2_000, ge=1, le=1_000_000)
    MAX_DATASET_NAME_CHARS: int = Field(default=100, ge=1, le=255)
    MAX_FILENAME_CHARS: int = Field(default=255, ge=1, le=300)

    # Optimization resource boundaries
    MAX_OPTIMIZATION_ROWS: int = Field(default=5_000, ge=1, le=100_000)
    MAX_MAX_ITEMS: int = Field(default=5_000, ge=1, le=100_000)
    DEFAULT_SOLVER_TIME_S: float = Field(default=5.0, ge=0.1, le=60.0)
    MAX_SOLVER_TIME_S: float = Field(default=10.0, ge=0.1, le=60.0)
    MAX_SOLVER_WORKERS: int = Field(default=2, ge=1, le=8)
    MAX_GLOBAL_OPTIMIZATIONS: int = Field(default=1, ge=1, le=32)
    MAX_NUMERIC_VALUE: float = Field(default=1_000_000_000_000.0, gt=0, le=1_000_000_000_000_000.0)

    # Rate-limiter storage boundary
    MAX_RATE_LIMIT_BUCKETS: int = Field(default=10_000, ge=100, le=1_000_000)

    # Unauthenticated authentication limits: keyed by client IP
    SIGNUP_RATE_LIMIT_REQUESTS: int = Field(default=5, ge=1, le=10_000)
    SIGNUP_RATE_LIMIT_WINDOW_S: int = Field(default=15 * 60, ge=1, le=86_400)
    LOGIN_RATE_LIMIT_REQUESTS: int = Field(default=10, ge=1, le=10_000)
    LOGIN_RATE_LIMIT_WINDOW_S: int = Field(default=5 * 60, ge=1, le=86_400)

    # Authenticated limits: keyed by user ID.
    UPLOAD_RATE_LIMIT_REQUESTS: int = Field(default=10, ge=1, le=100_000)
    UPLOAD_RATE_LIMIT_WINDOW_S: int = Field(default=60 * 60, ge=1, le=86_400)
    PREVIEW_RATE_LIMIT_REQUESTS: int = Field(default=60, ge=1, le=100_000)
    PREVIEW_RATE_LIMIT_WINDOW_S: int = Field(default=5 * 60, ge=1, le=86_400)
    RUN_CREATE_RATE_LIMIT_REQUESTS: int = Field(default=60, ge=1, le=100_000)
    RUN_CREATE_RATE_LIMIT_WINDOW_S: int = Field(default=60 * 60, ge=1, le=86_400)
    EXECUTE_RATE_LIMIT_REQUESTS: int = Field(default=12, ge=1, le=100_000)
    EXECUTE_RATE_LIMIT_WINDOW_S: int = Field(default=60 * 60, ge=1, le=86_400)
    AUTH_READ_RATE_LIMIT_REQUESTS: int = Field(default=120, ge=1, le=100_000)
    AUTH_READ_RATE_LIMIT_WINDOW_S: int = Field(default=60, ge=1, le=86_400)

    @model_validator(mode="after")
    def validate_settings(self) -> Self:
        minimum_request_size = self.MAX_UPLOAD_BYTES + _MULTIPART_OVERHEAD_ALLOWANCE

        if self.MAX_REQUEST_BYTES < minimum_request_size:
            raise ValueError("MAX_REQUEST_BYTES must exceed MAX_UPLOAD_BYTES by at least 65536 bytes for multipart request overhead.")

        if self.MAX_OPTIMIZATION_ROWS > self.MAX_DATASET_ROWS:
            raise ValueError("MAX_OPTIMIZATION_ROWS cannot exceed MAX_DATASET_ROWS.")

        if self.MAX_MAX_ITEMS > self.MAX_OPTIMIZATION_ROWS:
            raise ValueError("MAX_MAX_ITEMS cannot exceed MAX_OPTIMIZATION_ROWS.")

        if self.DEFAULT_SOLVER_TIME_S > self.MAX_SOLVER_TIME_S:
            raise ValueError("DEFAULT_SOLVER_TIME_S cannot exceed MAX_SOLVER_TIME_S.")

        session_secret = self.DO_SESSION_SECRET.strip()

        if len(session_secret) < _MIN_SESSION_SECRET_CHARS:
            raise ValueError(f"DO_SESSION_SECRET must be at least {_MIN_SESSION_SECRET_CHARS} characters.")

        if self.ENV.lower() in _PRODUCTION_ENVS and session_secret in _UNSAFE_PRODUCTION_SESSION_SECRETS:
            raise ValueError("DO_SESSION_SECRET must not use an example or test secret in production.")
        
        return self



settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")
