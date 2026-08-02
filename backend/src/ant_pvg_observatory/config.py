from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_prefix="ANT_PVG_", env_file=".env")

    app_name: str = "ANT–PVG Research Observatory"
    database_url: str = "sqlite:///./data/observatory.db"
    library_root: Path = Path("./library")
    allow_model_synthesis: bool = True

    # Server networking defaults; can be overridden via ANT_PVG_HOST / ANT_PVG_PORT
    host: str = "127.0.0.1"
    port: int = 8000


settings = Settings()
