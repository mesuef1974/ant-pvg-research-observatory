from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(env_prefix="ANT_PVG_", env_file=".env")

    app_name: str = "ANT–PVG Research Observatory"
    database_url: str = "sqlite:///./data/observatory.db"
    library_root: Path = Path("./library")
    allow_model_synthesis: bool = True


settings = Settings()
