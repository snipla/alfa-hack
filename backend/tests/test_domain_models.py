"""Проверки моделей без подключения к общей базе"""

from datetime import date, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import CheckConstraint, event, select, text
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import CreateIndex, CreateTable

from app.core.model_loader import include_model_object, load_models
from app.database.models.base import Base
from app.domains.applications.models import Application, ApplicationEvent
from app.domains.companies.models import Company, CompanyMembership
from app.domains.products.models import CreditProduct
from app.domains.scoring.models import ApplicationAssessment

load_models()


@pytest_asyncio.fixture
async def session():
    # Отдельная БД в памяти для каждого теста, без общих файлов и сервера.
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)

    @event.listens_for(engine.sync_engine, "connect")
    def foreign_keys_on(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    try:
        async with engine.begin() as connection:
            await connection.run_sync(Company.__table__.create)
            backend_tables = [
                table
                for table in Base.metadata.sorted_tables
                if include_model_object(table, table.name, "table", False, None)
            ]
            await connection.run_sync(
                lambda sync: Base.metadata.create_all(sync, tables=backend_tables)
            )
        async with AsyncSession(engine, expire_on_commit=False) as current:
            yield current
    finally:
        await engine.dispose()


async def make_company(session, **overrides):
    #     fields = {
    #         "inn": "0000000001",
    #         "name": "Демонстрационная компания",
    #         "legal_form": "legal_entity",
    #     }
    #     company = Company(**(fields | overrides))
    #     session.add(company)
    #     await session.flush()
    #     return company
    fields = {
        "inn": 123456789,
        "name": "Компания Laravel",
        "ogrn": 987654321,
        "registration_date": date(2020, 1, 1),
    }
    result = await session.execute(
        Company.__table__.insert().values(fields | overrides)
    )
    return await session.get(Company, result.inserted_primary_key[0])


async def make_product(session, **overrides):
    fields = {
        "code": "DEMO",
        "name": "Демонстрационный продукт",
        "min_amount": Decimal("100000.00"),
        "max_amount": Decimal("5000000.00"),
        "min_term_months": 6,
        "max_term_months": 36,
        "rules_version": "demo-v1",
    }
    product = CreditProduct(**(fields | overrides))
    session.add(product)
    await session.flush()
    return product


async def make_application(session):
    company = await make_company(session)
    product = await make_product(session)
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    await session.flush()
    application = Application(
        company_id=company.id,
        applicant_user_id=1,
        product_id=product.id,
        purpose="Оборотные средства",
        amount=Decimal("123456.78"),
        term_months=12,
        product_terms_snapshot={"code": product.code, "rules_version": "demo-v1"},
    )
    session.add(application)
    await session.flush()
    return application


def test_discovery_loads_business_models_without_manual_registry():
    expected = {
        "companies",
        "company_memberships",
        "credit_products",
        "applications",
        "application_assessments",
        "application_events",
    }
    assert expected <= set(Base.metadata.tables)
    assert "app.domains.companies.models" in load_models()
    assert load_models() == load_models()
    assert "users" not in Base.metadata.tables
    assert "roles" not in Base.metadata.tables


# @pytest.mark.parametrize("table_name", sorted(Base.metadata.tables))

@pytest.mark.parametrize(
    "table_name",
    sorted(
        name
        for name, table in Base.metadata.tables.items()
        if include_model_object(table, name, "table", False, None)
    ),
)
def test_mariadb_ddl_and_indexes_compile(table_name):
    table = Base.metadata.tables[table_name]
    ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
    assert "ENGINE=InnoDB" in ddl
    assert "utf8mb4" in ddl
    # assert "INTEGER" in ddl  # Ссылки на Laravel используют BIGINT UNSIGNED.
    assert "INTEGER" in ddl or "BIGINT" in ddl
    for index in table.indexes:
        assert "CREATE" in str(CreateIndex(index).compile(dialect=mysql.dialect()))
    for constraint in table.constraints:
        assert constraint.name is not None
    if table_name == "applications":
        assert "REFERENCES company_memberships (company_id, user_id)" in ddl
        assert "utf8mb4_bin" in ddl


def test_foreign_user_identifiers_do_not_recreate_laravel_accounts():
    assert not CompanyMembership.__table__.c.user_id.foreign_keys
    assert not Application.__table__.c.assigned_to_user_id.foreign_keys
    assert not ApplicationEvent.__table__.c.actor_user_id.foreign_keys


# @pytest.mark.asyncio
# async def test_company_defaults_leading_zeroes_and_utc_timestamps(session):
#     company = await make_company(session)
#     await session.commit()
#     saved_id = company.id
#     session.expire_all()
#     saved = await session.get(Company, saved_id)
#     assert saved.inn == "0000000001"
#     assert saved.is_active is True
#     assert saved.created_at.tzinfo is None
#     assert saved.updated_at.tzinfo is None


# @pytest.mark.parametrize(
#     "fields",
#     [
#         {"inn": "123"},
#         {"inn": "000000000X"},
#         {"inn": "0000000001\n"},
#         {"legal_form": "individual_entrepreneur", "inn": "0000000001"},
#         {"legal_form": "unknown"},
#         {"legal_form": "LEGAL_ENTITY"},
#         {"ogrn": "000000000000001"},
#     ],
# )
# @pytest.mark.asyncio
# async def test_invalid_company_identifiers_are_rejected(session, fields):
#     with pytest.raises(IntegrityError):
#         await make_company(session, **fields)


# @pytest.mark.asyncio
# async def test_individual_entrepreneur_identifiers_fit(session):
#     company = await make_company(
#         session,
#         legal_form="individual_entrepreneur",
#         inn="000000000001",
#         ogrn="000000000000001",
#     )
#     assert company.legal_form == "individual_entrepreneur"


# @pytest.mark.asyncio
# async def test_company_identifier_is_unique(session):
#     await make_company(session)
#     with pytest.raises(IntegrityError):
#         await make_company(session)


@pytest.mark.asyncio
async def test_membership_pair_is_unique(session):
    company = await make_company(session)
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    await session.flush()
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.parametrize(
    "fields",
    [
        {"min_amount": Decimal(-1)},
        {"min_amount": Decimal(6000000)},
        {"min_term_months": 0},
        {"max_term_months": 1},
        {"annual_rate_percent": Decimal("-0.01")},
        {"currency": "rub"},
        {"currency": "RU"},
    ],
)
@pytest.mark.asyncio
async def test_invalid_product_conditions_are_rejected(session, fields):
    with pytest.raises(IntegrityError):
        await make_product(session, **fields)


@pytest.mark.asyncio
async def test_application_requires_membership_for_same_company_and_user(session):
    application = await make_application(session)
    await session.commit()
    application.applicant_user_id = 2
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_membership_used_by_application_cannot_be_deleted(session):
    application = await make_application(session)
    await session.commit()
    membership = await session.get(
        CompanyMembership, (application.company_id, application.applicant_user_id)
    )
    await session.delete(membership)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_application_money_defaults_and_snapshot_are_persisted(session):
    application = await make_application(session)
    await session.commit()
    product = await session.get(CreditProduct, application.product_id)
    product.rules_version = "demo-v2"
    await session.commit()
    saved_id = application.id
    session.expire_all()
    saved = await session.get(Application, saved_id)
    assert saved.amount == Decimal("123456.78")
    assert saved.status == "draft"
    assert saved.version == 1
    assert saved.currency == "RUB"
    assert saved.product_terms_snapshot["rules_version"] == "demo-v1"


@pytest.mark.parametrize(
    "field, value",
    [
        ("amount", Decimal(0)),
        ("term_months", 0),
        ("version", 0),
        ("status", "unknown"),
        ("status", "APPROVED"),
        ("currency", "rub"),
        ("consent_version", "v1"),
    ],
)
@pytest.mark.asyncio
async def test_invalid_application_values_are_rejected(session, field, value):
    application = await make_application(session)
    await session.commit()
    setattr(application, field, value)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_assessment_snapshots_and_probability_roundtrip(session):
    application = await make_application(session)
    assessment = ApplicationAssessment(
        application_id=application.id,
        attempt_no=1,
        status="succeeded",
        model_version="demo-v1",
        features_snapshot={"loan_purpose": "working_capital", "business_scale": 1},
        probability_value=Decimal("0.123456"),
        probability_kind="default_probability",
        result_snapshot={"cluster": 2},
    )
    session.add(assessment)
    await session.commit()
    saved_id = assessment.id
    session.expire_all()
    saved = await session.get(ApplicationAssessment, saved_id)
    assert saved.probability_value == Decimal("0.123456")
    assert saved.features_snapshot["business_scale"] == 1
    assert saved.result_snapshot == {"cluster": 2}


@pytest.mark.parametrize(
    "fields",
    [
        {
            "probability_value": Decimal("-0.000001"),
            "probability_kind": "default_probability",
        },
        {
            "probability_value": Decimal("1.000001"),
            "probability_kind": "default_probability",
        },
        {"probability_value": Decimal("0.5")},
        {"probability_kind": "default_probability"},
        {"probability_value": Decimal("0.5"), "probability_kind": "unknown"},
        {"risk_level": "unknown"},
        {"recommendation": "unknown"},
        {"attempt_no": 0},
    ],
)
@pytest.mark.asyncio
async def test_invalid_assessment_values_are_rejected(session, fields):
    application = await make_application(session)
    assessment = ApplicationAssessment(
        **({"application_id": application.id, "attempt_no": 1} | fields)
    )
    session.add(assessment)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_assessment_attempt_number_is_unique_per_application(session):
    application = await make_application(session)
    session.add_all(
        [
            ApplicationAssessment(application_id=application.id, attempt_no=1),
            ApplicationAssessment(application_id=application.id, attempt_no=1),
        ]
    )
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_history_supports_system_actor_and_rejects_unknown_status(session):
    application = await make_application(session)
    entry = ApplicationEvent(
        application_id=application.id,
        event_type="created",
        to_status="draft",
        metadata_json={"source": "demo"},
    )
    session.add(entry)
    await session.commit()
    assert entry.actor_user_id is None
    entry.to_status = "unknown"
    with pytest.raises(IntegrityError):
        await session.flush()


# @pytest.mark.asyncio
# async def test_timestamp_updates_on_orm_change(session):
#     company = await make_company(session)
#     company.updated_at = datetime(2000, 1, 1)
#     await session.commit()
#     company.name = "Новое название"
#     await session.commit()
#     await session.refresh(company)
#     assert company.updated_at > datetime(2000, 1, 1)


def test_named_check_constraints_match_existing_base_convention():
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if isinstance(constraint, CheckConstraint):
                assert constraint.name.startswith(f"ck_{table.name}_")


@pytest.mark.asyncio
async def test_alembic_ignores_laravel_tables_and_only_manages_business_models(session):
    connection = await session.connection()
    await connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
    await connection.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY)"))

    def compare(sync_connection):
        context = MigrationContext.configure(
            sync_connection,
            opts={"include_object": include_model_object, "compare_type": True},
        )
        return compare_metadata(context, Base.metadata)

    assert await connection.run_sync(compare) == []
    assert include_model_object(None, "users", "table", True, None) is False
    # assert include_model_object(None, "companies", "table", True, None) is True
    assert include_model_object(None, "companies", "table", True, None) is False


@pytest.mark.asyncio
async def test_new_attempt_defaults_to_queued(session):
    application = await make_application(session)
    assessment = ApplicationAssessment(application_id=application.id, attempt_no=1)
    session.add(assessment)
    await session.flush()
    assert assessment.status == "queued"
    assert await session.scalar(select(ApplicationAssessment.id)) == assessment.id


@pytest.mark.asyncio
async def test_laravel_company_mapping_reads_existing_fields(session):
    company = await make_company(session)
    assert company.inn == 123456789
    assert company.ogrn == 987654321
    assert company.registration_date == date(2020, 1, 1)
    assert company.created_at is None
    assert company.updated_at is None
    assert Company.__table__.info["managed_by"] == "laravel"
    assert "legal_form" not in Company.__table__.c
    assert "okved_code" not in Company.__table__.c
    assert "is_active" not in Company.__table__.c


@pytest.mark.asyncio
async def test_backend_timestamp_updates_on_product_change(session):
    product = await make_product(session)
    product.updated_at = datetime(2000, 1, 1)
    await session.commit()
    product.name = "Новое название"
    await session.commit()
    await session.refresh(product)
    assert product.updated_at > datetime(2000, 1, 1)


@pytest.mark.parametrize("laravel_table_exists", [False, True])
@pytest.mark.asyncio
async def test_alembic_never_creates_or_changes_laravel_companies(laravel_table_exists):
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    try:
        async with engine.begin() as connection:
            if laravel_table_exists:
                # Намеренно другая структура: Alembic не должен её исправлять.
                await connection.execute(
                    text(
                        "CREATE TABLE companies (id INTEGER PRIMARY KEY, laravel_extra TEXT)"
                    )
                )
                await connection.execute(
                    text(
                        "CREATE INDEX laravel_extra_index ON companies (laravel_extra)"
                    )
                )

            def compare(sync):
                context = MigrationContext.configure(
                    sync,
                    opts={
                        "include_object": include_model_object,
                        "compare_type": True,
                    },
                )
                return compare_metadata(context, Base.metadata)

            differences = await connection.run_sync(compare)
            # Новые собственные таблицы также создают свои индексы.
            assert all(item[0] in {"add_table", "add_index"} for item in differences)
            assert {item[1].name for item in differences if item[0] == "add_table"} == {
                "company_memberships",
                "credit_products",
                "applications",
                "application_assessments",
                "application_events",
            }
            assert all(
                item[1].table.name != "companies"
                for item in differences
                if item[0] == "add_index"
            )
    finally:
        await engine.dispose()


def test_company_foreign_keys_match_laravel_unsigned_bigint():
    dialect = mysql.dialect()
    for table, column in (
        (Company.__table__, "id"),
        (CompanyMembership.__table__, "company_id"),
        (Application.__table__, "company_id"),
    ):
        assert table.c[column].type.compile(dialect=dialect) == "BIGINT UNSIGNED"
    for column in Company.__table__.c:
        assert column.default is None
        assert column.onupdate is None
        assert not include_model_object(column, column.name, "column", False, column)
