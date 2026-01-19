from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Backend API"
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str

    # SMTP (MailHog)
    SMTP_HOST: str = "mailhog"
    SMTP_PORT: int = 1025

    # S3 (MinIO)
    S3_ENDPOINT: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "app-bucket"

    # Environment
    ENV: str = "development"


settings = Settings()
