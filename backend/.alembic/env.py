import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from pydantic import MySQLDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.model_loader import include_model_object, load_models
from app.database.models.base import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


class MigrationSettings(BaseSettings):
    DATABASE_URL: MySQLDsn
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")


# Переданное соединение позволяет тестировать upgrade/downgrade без общей БД.
provided_connection = config.attributes.get("connection")
if provided_connection is None:
    url = config.attributes.get("database_url")
    if url is None:
        backend_path = Path(config.config_file_name).resolve().parent
        url = str(MigrationSettings(_env_file=backend_path / ".env").DATABASE_URL)
    config.set_main_option("sqlalchemy.url", str(url).replace("%", "%%"))

load_models()
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_model_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_model_object,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
elif provided_connection is not None:
    do_run_migrations(provided_connection)
else:
    asyncio.run(run_migrations_online())
