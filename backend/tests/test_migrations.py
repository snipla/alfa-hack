"""Реальные команды Alembic на отдельной БД; общая база не используется."""

import ast
from io import StringIO
from pathlib import Path

import pytest
import pytest_asyncio
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.model_loader import include_model_object, load_models
from app.database.models.base import Base

BACKEND = Path(__file__).resolve().parents[1]
REVISION = "20261026_01"
OWNED_TABLES = {
    "company_memberships",
    "credit_products",
    "applications",
    "application_assessments",
    "application_events",
}
LARAVEL_TABLES = {"companies", "users", "roles", "requests", "migrations"}


def config_for(connection=None):
    config = Config(str(BACKEND / "alembic.ini"))
    if connection is not None:
        config.attributes["connection"] = connection
    return config


def upgrade(connection):
    command.upgrade(config_for(connection), "head")


def downgrade(connection):
    command.downgrade(config_for(connection), "base")


@pytest_asyncio.fixture
async def connection():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

    @sa.event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi, _record):
        cursor = dbapi.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    try:
        async with engine.begin() as current:
            yield current
    finally:
        await engine.dispose()


async def create_laravel_tables(connection):
    # Независимая фикстура Laravel: намеренно не создаём её из Company metadata.
    await connection.execute(
        sa.text("""
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY, name VARCHAR(255) NOT NULL,
            inn INTEGER NOT NULL, ogrn INTEGER NOT NULL,
            registration_date DATE NOT NULL, created_at DATETIME,
            updated_at DATETIME, laravel_note TEXT
        )
    """)
    )
    await connection.execute(
        sa.text("""
        INSERT INTO companies (id, name, inn, ogrn, registration_date, laravel_note)
        VALUES (5000000000, 'Laravel company', 123456789, 987654321,
                '2020-01-01', 'keep unchanged')
    """)
    )
    for table in sorted(LARAVEL_TABLES - {"companies"}):
        await connection.execute(
            sa.text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, note TEXT)")
        )
        await connection.execute(
            sa.text(f"INSERT INTO {table} (id, note) VALUES (7, 'keep unchanged')")
        )
    await connection.execute(
        sa.text("CREATE INDEX ix_laravel_company_name ON companies (name)")
    )


def laravel_snapshot(connection):
    inspector = sa.inspect(connection)
    return {
        table: (
            tuple(connection.execute(sa.text(f"SELECT * FROM {table}")).all()),
            tuple(
                (col["name"], str(col["type"]), col["nullable"])
                for col in inspector.get_columns(table)
            ),
            tuple(index["name"] for index in inspector.get_indexes(table)),
        )
        for table in sorted(LARAVEL_TABLES)
    }


@pytest.mark.asyncio
async def test_upgrade_downgrade_and_reupgrade_preserve_laravel(connection):
    await create_laravel_tables(connection)
    before = await connection.run_sync(laravel_snapshot)
    await connection.run_sync(upgrade)

    def inspect_upgraded(sync):
        inspector = sa.inspect(sync)
        assert set(inspector.get_table_names()) == OWNED_TABLES | LARAVEL_TABLES | {
            "alembic_version"
        }
        assert MigrationContext.configure(sync).get_current_revision() == REVISION
        load_models()
        assert (
            compare_metadata(
                MigrationContext.configure(
                    sync,
                    opts={
                        "include_object": include_model_object,
                        "compare_type": True,
                    },
                ),
                Base.metadata,
            )
            == []
        )
        for name in OWNED_TABLES:
            names = [item["name"] for item in inspector.get_check_constraints(name)]
            assert len(names) == len(set(names)), (name, names)
        for name in ("credit_products", "company_memberships"):
            names = [item["name"] for item in inspector.get_check_constraints(name)]
            assert names.count(f"ck_{name}_is_active") == 1

    await connection.run_sync(inspect_upgraded)
    assert await connection.run_sync(laravel_snapshot) == before
    # Повторный upgrade head не выполняет ту же ревизию второй раз.
    await connection.run_sync(upgrade)
    await connection.run_sync(downgrade)
    assert set(
        await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names())
    ) == LARAVEL_TABLES | {"alembic_version"}
    assert await connection.run_sync(laravel_snapshot) == before
    await connection.run_sync(upgrade)
    await connection.run_sync(inspect_upgraded)
    assert await connection.run_sync(laravel_snapshot) == before


@pytest.mark.asyncio
async def test_upgrade_fails_before_creating_backend_without_companies(connection):
    with pytest.raises(RuntimeError, match="Laravel"):
        await connection.run_sync(upgrade)
    names = set(
        await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names())
    )
    assert not names & OWNED_TABLES
    assert "companies" not in names


@pytest.mark.asyncio
async def test_upgrade_rejects_incompatible_company_primary_key(connection):
    await connection.execute(
        sa.text("CREATE TABLE companies (other_id INTEGER PRIMARY KEY)")
    )
    with pytest.raises(RuntimeError, match="первичный ключ id"):
        await connection.run_sync(upgrade)
    names = set(
        await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names())
    )
    assert not names & OWNED_TABLES


@pytest.mark.asyncio
async def test_upgrade_refuses_existing_unversioned_backend_table(connection):
    await create_laravel_tables(connection)
    await connection.execute(
        sa.text("CREATE TABLE credit_products (id INTEGER PRIMARY KEY)")
    )
    await connection.execute(sa.text("INSERT INTO credit_products (id) VALUES (99)"))
    before = await connection.run_sync(laravel_snapshot)
    with pytest.raises(RuntimeError, match="credit_products"):
        await connection.run_sync(upgrade)
    names = set(
        await connection.run_sync(lambda sync: sa.inspect(sync).get_table_names())
    )
    assert names & OWNED_TABLES == {"credit_products"}
    assert await connection.scalar(sa.text("SELECT id FROM credit_products")) == 99
    assert await connection.run_sync(laravel_snapshot) == before


@pytest.mark.parametrize("direction", ["upgrade", "downgrade"])
def test_offline_mysql_sql_changes_only_backend_tables(direction, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://test:test@localhost/test_db")
    for key in ("SYSTEM_API_KEY", "CORS_ORIGINS", "ML_API_URL", "DEV"):
        monkeypatch.delenv(key, raising=False)
    output = StringIO()
    config = config_for()
    config.output_buffer = output
    if direction == "upgrade":
        command.upgrade(config, "head", sql=True)
    else:
        command.downgrade(config, f"{REVISION}:base", sql=True)
    sql = output.getvalue()
    assert "BIGINT UNSIGNED" in sql if direction == "upgrade" else "DROP TABLE" in sql
    for name in LARAVEL_TABLES:
        assert f"CREATE TABLE {name} " not in sql
        assert f"DROP TABLE {name};" not in sql
        assert f"ALTER TABLE {name} " not in sql
    if direction == "upgrade":
        assert "REFERENCES companies (id)" in sql
        for name in OWNED_TABLES:
            assert f"CREATE TABLE {name} " in sql
        assert "ENGINE=InnoDB" in sql
        assert "utf8mb4_bin" in sql


def test_revision_is_frozen_and_does_not_import_app_models():
    path = BACKEND / ".alembic/versions/20261026_01_create_backend_tables.py"
    module = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(module):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("app")
        if isinstance(node, ast.Import):
            assert all(not alias.name.startswith("app") for alias in node.names)
