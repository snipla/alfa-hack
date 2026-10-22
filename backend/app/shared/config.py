from pydantic import MySQLDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SYSTEM_API_KEY: SecretStr
    CORS_ORIGINS: list[str]

    ML_API_URL: str = "http://backend-ml:8000"
    DATABASE_URL: MySQLDsn = MySQLDsn(
        "mysql+asyncmy://user:password@localhost:3306/database"
    )

    DEV: bool

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
