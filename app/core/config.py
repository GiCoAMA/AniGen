from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_title: str = "AniGen"
    # Development DB (SQLite). Production can pass a PostgreSQL URL.
    # Example (PostgreSQL): `postgresql+asyncpg://user:pass@host:5432/dbname`
    database_url: str = "sqlite:///./anigen.db"
    redis_host: str = "localhost"
    redis_port: int = 6379
    # Stable Diffusion WebUI txt2img API. Override with env `SD_API_URL`.
    sd_api_url: str = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()

