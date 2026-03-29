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
    # SD WebUI base URL (no path). Docker: host via host.docker.internal. Override with env `SD_WEBUI_URL`.
    sd_webui_url: str = "http://host.docker.internal:7860"
    host: str = "0.0.0.0"
    port: int = 8000

    # JWT / password hashing (override SECRET_KEY in production).
    secret_key: str = (
        "0f8e9d7c6b5a4938271605f4e3d2c1b0a9f8e7d6c5b4a3928170654435241302"
        "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0011223344556677"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # Image persistence: "local" | "oss" | "s3" (only local implemented).
    storage_backend: str = "local"


settings = Settings()
