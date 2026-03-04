from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "DecisionOps"
    ENV: str = "production"
    DATABASE_URL: str = ""
    DO_SESSION_SECRET: str = ""


settings = Settings()

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required")
if not settings.DO_SESSION_SECRET:
    raise RuntimeError("DO_SESSION_SECRET is required")