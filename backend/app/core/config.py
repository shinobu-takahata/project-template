from typing import Optional
from pydantic import ConfigDict, computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "Backend API"
    API_V1_STR: str = "/api/v1"

    # Database - Individual components (for ECS deployment)
    DATABASE_HOST: Optional[str] = None
    DATABASE_PORT: Optional[int] = None
    DATABASE_NAME: Optional[str] = None
    DATABASE_USER: Optional[str] = None
    DATABASE_PASSWORD: Optional[str] = None

    # Database - Full URL (for local development)
    _DATABASE_URL: Optional[str] = None

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

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """
        Build DATABASE_URL from individual components if available,
        otherwise use the direct URL or return test default.
        """
        # If _DATABASE_URL is explicitly set (e.g., from .env), use it
        if self._DATABASE_URL:
            return self._DATABASE_URL

        # If individual components are set (ECS deployment), build URL
        if all([self.DATABASE_HOST, self.DATABASE_PORT, self.DATABASE_NAME,
                self.DATABASE_USER, self.DATABASE_PASSWORD]):
            # パスワードに%がある場合は%%にエスケープ（ConfigParser対策）
            escaped_password = self.DATABASE_PASSWORD.replace('%', '%%')
            return (
                f"postgresql://{self.DATABASE_USER}:{escaped_password}"
                f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
            )

        # Default fallback for tests
        return "postgresql://localhost/test"


settings = Settings()
