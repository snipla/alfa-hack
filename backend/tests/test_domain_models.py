"""Проверки моделей без подключения к общей базе"""

from datetime import datetime
from decimal import Decimal

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import CheckConstraint, create_engine, event, select, text
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database.models.registry import (
    MANAGED_TABLES,
    Application,
    ApplicationAssessment,
    ApplicationEvent,
    Base,
    Company,
    CompanyMembership,
    CreditProduct,
    include_model_object,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def foreign_keys_on(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as current:
            yield current
    finally:
        engine.dispose()


def make_company(session, **overrides):
    fields = {
        "inn": "0000000001",
        "name": "Демонстрационная компания",
        "legal_form": "legal_entity",
    }
    company = Company(**(fields | overrides))
    session.add(company)
    session.flush()
    return company


def make_product(session, **overrides):
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
    session.flush()
    return product


def make_application(session):
    company = make_company(session)
    product = make_product(session)
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    session.flush()
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
    session.flush()
    return application


def test_registry_only_contains_business_tables():
    assert set(Base.metadata.tables) == MANAGED_TABLES
    assert len(MANAGED_TABLES) == 6
    assert "users" not in Base.metadata.tables
    assert "roles" not in Base.metadata.tables


@pytest.mark.parametrize("table_name", sorted(MANAGED_TABLES))
def test_mariadb_ddl_and_indexes_compile(table_name):
    table = Base.metadata.tables[table_name]
    ddl = str(CreateTable(table).compile(dialect=mysql.dialect()))
    assert "ENGINE=InnoDB" in ddl
    assert "utf8mb4" in ddl
    assert "BIGINT UNSIGNED" in ddl
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


def test_company_defaults_leading_zeroes_and_utc_timestamps(session):
    company = make_company(session)
    session.commit()
    session.expire_all()
    saved = session.get(Company, company.id)
    assert saved.inn == "0000000001"
    assert saved.is_active is True
    assert saved.created_at.tzinfo is None
    assert saved.updated_at.tzinfo is None


@pytest.mark.parametrize(
    "fields",
    [
        {"inn": "123"},
        {"inn": "000000000X"},
        {"inn": "0000000001\n"},
        {"legal_form": "individual_entrepreneur", "inn": "0000000001"},
        {"legal_form": "unknown"},
        {"legal_form": "LEGAL_ENTITY"},
        {"ogrn": "000000000000001"},
    ],
)
def test_invalid_company_identifiers_are_rejected(session, fields):
    with pytest.raises(IntegrityError):
        make_company(session, **fields)


def test_individual_entrepreneur_identifiers_fit(session):
    company = make_company(
        session,
        legal_form="individual_entrepreneur",
        inn="000000000001",
        ogrn="000000000000001",
    )
    assert company.legal_form == "individual_entrepreneur"


def test_company_identifier_is_unique(session):
    make_company(session)
    with pytest.raises(IntegrityError):
        make_company(session)


def test_membership_pair_is_unique(session):
    company = make_company(session)
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    session.flush()
    session.add(CompanyMembership(company_id=company.id, user_id=1))
    with pytest.raises(IntegrityError):
        session.flush()


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
def test_invalid_product_conditions_are_rejected(session, fields):
    with pytest.raises(IntegrityError):
        make_product(session, **fields)


def test_application_requires_membership_for_same_company_and_user(session):
    application = make_application(session)
    session.commit()
    application.applicant_user_id = 2
    with pytest.raises(IntegrityError):
        session.flush()


def test_membership_used_by_application_cannot_be_deleted(session):
    application = make_application(session)
    session.commit()
    membership = session.get(
        CompanyMembership, (application.company_id, application.applicant_user_id)
    )
    session.delete(membership)
    with pytest.raises(IntegrityError):
        session.flush()


def test_application_money_defaults_and_snapshot_are_persisted(session):
    application = make_application(session)
    session.commit()
    product = session.get(CreditProduct, application.product_id)
    product.rules_version = "demo-v2"
    session.commit()
    session.expire_all()
    saved = session.get(Application, application.id)
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
def test_invalid_application_values_are_rejected(session, field, value):
    application = make_application(session)
    session.commit()
    setattr(application, field, value)
    with pytest.raises(IntegrityError):
        session.flush()


def test_assessment_snapshots_and_probability_roundtrip(session):
    application = make_application(session)
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
    session.commit()
    session.expire_all()
    saved = session.get(ApplicationAssessment, assessment.id)
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
def test_invalid_assessment_values_are_rejected(session, fields):
    application = make_application(session)
    assessment = ApplicationAssessment(
        **({"application_id": application.id, "attempt_no": 1} | fields)
    )
    session.add(assessment)
    with pytest.raises(IntegrityError):
        session.flush()


def test_assessment_attempt_number_is_unique_per_application(session):
    application = make_application(session)
    session.add_all(
        [
            ApplicationAssessment(application_id=application.id, attempt_no=1),
            ApplicationAssessment(application_id=application.id, attempt_no=1),
        ]
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_history_supports_system_actor_and_rejects_unknown_status(session):
    application = make_application(session)
    entry = ApplicationEvent(
        application_id=application.id,
        event_type="created",
        to_status="draft",
        metadata_json={"source": "demo"},
    )
    session.add(entry)
    session.commit()
    assert entry.actor_user_id is None
    entry.to_status = "unknown"
    with pytest.raises(IntegrityError):
        session.flush()


def test_timestamp_updates_on_orm_change(session):
    company = make_company(session)
    company.updated_at = datetime(2000, 1, 1)
    session.commit()
    company.name = "Новое название"
    session.commit()
    assert company.updated_at > datetime(2000, 1, 1)


def test_named_check_constraints_match_existing_base_convention():
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if isinstance(constraint, CheckConstraint):
                assert constraint.name.startswith(f"ck_{table.name}_")


def test_alembic_ignores_laravel_tables_and_only_manages_business_models(session):
    connection = session.connection()
    connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))
    connection.execute(text("CREATE TABLE roles (id INTEGER PRIMARY KEY)"))
    context = MigrationContext.configure(
        connection,
        opts={
            "include_object": include_model_object,
            "compare_type": True,
        },
    )
    assert compare_metadata(context, Base.metadata) == []
    assert include_model_object(None, "users", "table", True, None) is False
    assert include_model_object(None, "companies", "table", True, None) is True


def test_new_attempt_defaults_to_queued(session):
    application = make_application(session)
    assessment = ApplicationAssessment(application_id=application.id, attempt_no=1)
    session.add(assessment)
    session.flush()
    assert assessment.status == "queued"
    assert session.scalar(select(ApplicationAssessment.id)) == assessment.id
