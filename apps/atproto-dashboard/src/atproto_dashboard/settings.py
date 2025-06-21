from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        # Load from workspace root .env file
        env_file=Path(__file__).parent.parent.parent.parent.parent / ".env",
        extra="ignore",
    )

    # Bluesky credentials
    bsky_login: str = ""
    bsky_app_password: str = ""

    # AWS settings (bucket name only - credentials from ~/.aws/credentials)
    aws_bucket_name: str = "prefect-demo"

    # dbt settings
    dbt_target: str = "dev"


# Global settings instance
settings = Settings()
