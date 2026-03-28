from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    app_title: str = "AniGen"
    # SQLite in Docker: absolute path /app/data (four slashes after scheme). Override via DATABASE_URL.
    # Example (PostgreSQL): `postgresql+asyncpg://user:pass@host:5432/dbname`
    database_url: str = "sqlite+aiosqlite:////app/data/anigen.db"
    redis_host: str = "localhost"
    redis_port: int = 6379
    # Stable Diffusion WebUI txt2img API. Override with env `SD_API_URL`.
    sd_api_url: str = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
