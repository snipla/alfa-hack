from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SHARED_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = SHARED_DIR / "models" / "model-test.cbm"


class Settings(BaseSettings):
    CORS_ORIGINS: list[str]

    API_KEY_SALT: SecretStr
    SYSTEM_API_KEY_HASH: SecretStr
    DEV: bool

    MODEL_PATH: Path = DEFAULT_MODEL_PATH
    MODEL_THREAD_COUNT: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
