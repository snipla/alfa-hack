"""Создание таблиц кредитного кабинета, принадлежащих Python backend.

Revision ID: 20261026_01
Revises: None
companies должна быть создана миграциями Laravel до этой ревизии.
"""

import sqlalchemy as sa
from alembic import context, op
from sqlalchemy.dialects import mysql

revision = "20261026_01"
down_revision = None
branch_labels = None
depends_on = None

BACKEND_TABLES = (
    "company_memberships",
    "credit_products",
    "applications",
    "application_assessments",
    "application_events",
)


def _check_prerequisites() -> None:
    """Проверяем зависимости до первого CREATE: DDL MariaDB не транзакционен."""
    if context.is_offline_mode():
        return
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    if not inspector.has_table("companies"):
        raise RuntimeError(
            "Сначала выполните Laravel-миграцию companies. "
            "Эта ревизия не создаёт таблицы Laravel."
        )
    columns = {column["name"]: column for column in inspector.get_columns("companies")}
    if "id" not in columns or inspector.get_pk_constraint("companies")[
        "constrained_columns"
    ] != ["id"]:
        raise RuntimeError(
            "companies должна иметь первичный ключ id из Laravel-миграции."
        )
    if connection.dialect.name in {"mysql", "mariadb"}:
        id_type = columns["id"]["type"]
        if not isinstance(id_type, sa.BigInteger) or not getattr(
            id_type, "unsigned", False
        ):
            raise RuntimeError("companies.id должен иметь тип BIGINT UNSIGNED.")
        options = inspector.get_table_options("companies")
        engine = options.get("mysql_engine", options.get("mariadb_engine", ""))
        if engine.lower() != "innodb":
            raise RuntimeError(
                "companies должна использовать InnoDB для внешнего ключа."
            )
    existing = sorted(set(inspector.get_table_names()) & set(BACKEND_TABLES))
    if existing:
        raise RuntimeError(
            "Найдены таблицы backend без этой ревизии: "
            + ", ".join(existing)
            + ". Сначала проверьте историю Alembic и существующую схему."
        )


def upgrade() -> None:
    _check_prerequisites()
    op.create_table(
        "credit_products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "code",
            sa.String(length=50, collation="utf8mb4_bin").with_variant(
                sa.String(length=50, collation="BINARY"), "sqlite"
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3, collation="utf8mb4_bin").with_variant(
                sa.String(length=3, collation="BINARY"), "sqlite"
            ),
            server_default=sa.text("'RUB'"),
            nullable=False,
        ),
        sa.Column("min_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("max_amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column("min_term_months", sa.Integer(), nullable=False),
        sa.Column("max_term_months", sa.Integer(), nullable=False),
        sa.Column(
            "annual_rate_percent", sa.Numeric(precision=7, scale=4), nullable=True
        ),
        sa.Column("rules_json", sa.JSON(), nullable=True),
        sa.Column("rules_version", sa.String(length=50), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency REGEXP '^[A-Z]{3}$'",
            name=op.f("ck_credit_products_currency_format"),
        ),
        sa.CheckConstraint(
            "annual_rate_percent IS NULL OR annual_rate_percent >= 0",
            name=op.f("ck_credit_products_annual_rate"),
        ),
        sa.CheckConstraint(
            "is_active IN (0, 1)", name=op.f("ck_credit_products_is_active")
        ),
        sa.CheckConstraint(
            "min_amount > 0 AND max_amount >= min_amount",
            name=op.f("ck_credit_products_amount_range"),
        ),
        sa.CheckConstraint(
            "min_term_months > 0 AND max_term_months >= min_term_months",
            name=op.f("ck_credit_products_term_range"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_credit_products")),
        sa.UniqueConstraint("code", name=op.f("uq_credit_products_code")),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
    )
    op.create_table(
        "company_memberships",
        sa.Column(
            "company_id",
            mysql.BIGINT(unsigned=True).with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "is_active IN (0, 1)", name=op.f("ck_company_memberships_is_active")
        ),
        sa.CheckConstraint(
            "user_id > 0", name=op.f("ck_company_memberships_positive_user_id")
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_company_memberships_company_id_companies"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "company_id", "user_id", name=op.f("pk_company_memberships")
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        op.f("ix_company_memberships_user_id"),
        "company_memberships",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "company_id",
            mysql.BIGINT(unsigned=True).with_variant(sa.Integer(), "sqlite"),
            nullable=False,
        ),
        sa.Column("applicant_user_id", sa.BigInteger(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("assigned_to_user_id", sa.BigInteger(), nullable=True),
        sa.Column("purpose", sa.String(length=500), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3, collation="utf8mb4_bin").with_variant(
                sa.String(length=3, collation="BINARY"), "sqlite"
            ),
            server_default=sa.text("'RUB'"),
            nullable=False,
        ),
        sa.Column("term_months", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30, collation="utf8mb4_bin").with_variant(
                sa.String(length=30, collation="BINARY"), "sqlite"
            ),
            server_default=sa.text("'draft'"),
            nullable=False,
        ),
        sa.Column("product_terms_snapshot", sa.JSON(), nullable=False),
        sa.Column("consent_version", sa.String(length=50), nullable=True),
        sa.Column("consented_at", sa.DateTime(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("decision_comment", sa.Text(), nullable=True),
        sa.Column("signed_at", sa.DateTime(), nullable=True),
        sa.Column("disbursed_at", sa.DateTime(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency REGEXP '^[A-Z]{3}$'",
            name=op.f("ck_applications_currency_format"),
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'submitted', 'in_review', 'approved', 'rejected', 'signed', 'disbursed')",
            name=op.f("ck_applications_status"),
        ),
        sa.CheckConstraint(
            "(consent_version IS NULL AND consented_at IS NULL) OR (consent_version IS NOT NULL AND consented_at IS NOT NULL)",
            name=op.f("ck_applications_consent_pair"),
        ),
        sa.CheckConstraint("amount > 0", name=op.f("ck_applications_positive_amount")),
        sa.CheckConstraint(
            "assigned_to_user_id IS NULL OR assigned_to_user_id > 0",
            name=op.f("ck_applications_positive_assignee"),
        ),
        sa.CheckConstraint(
            "term_months > 0", name=op.f("ck_applications_positive_term")
        ),
        sa.CheckConstraint(
            "version > 0", name=op.f("ck_applications_positive_version")
        ),
        sa.ForeignKeyConstraint(
            ["company_id", "applicant_user_id"],
            ["company_memberships.company_id", "company_memberships.user_id"],
            name=op.f("fk_applications_company_id_company_memberships"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["credit_products.id"],
            name=op.f("fk_applications_product_id_credit_products"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        op.f("ix_applications_applicant_user_id"),
        "applications",
        ["applicant_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_applications_assignee_status",
        "applications",
        ["assigned_to_user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_applications_company_created",
        "applications",
        ["company_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_product_id"), "applications", ["product_id"], unique=False
    )
    op.create_index(
        "ix_applications_status_created",
        "applications",
        ["status", "created_at"],
        unique=False,
    )
    op.create_table(
        "application_assessments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20, collation="utf8mb4_bin").with_variant(
                sa.String(length=20, collation="BINARY"), "sqlite"
            ),
            server_default=sa.text("'queued'"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("feature_schema_version", sa.String(length=50), nullable=True),
        sa.Column("source_snapshot", sa.JSON(), nullable=True),
        sa.Column("features_snapshot", sa.JSON(), nullable=True),
        sa.Column("result_snapshot", sa.JSON(), nullable=True),
        sa.Column("probability_value", sa.Numeric(precision=7, scale=6), nullable=True),
        sa.Column(
            "probability_kind",
            sa.String(length=30, collation="utf8mb4_bin").with_variant(
                sa.String(length=30, collation="BINARY"), "sqlite"
            ),
            nullable=True,
        ),
        sa.Column(
            "risk_level",
            sa.String(length=20, collation="utf8mb4_bin").with_variant(
                sa.String(length=20, collation="BINARY"), "sqlite"
            ),
            nullable=True,
        ),
        sa.Column(
            "recommendation",
            sa.String(length=30, collation="utf8mb4_bin").with_variant(
                sa.String(length=30, collation="BINARY"), "sqlite"
            ),
            nullable=True,
        ),
        sa.Column("explanation", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(probability_value IS NULL AND probability_kind IS NULL) OR (probability_value IS NOT NULL AND probability_value BETWEEN 0 AND 1 AND probability_kind IS NOT NULL AND probability_kind IN ('default_probability', 'approval_probability'))",
            name=op.f("ck_application_assessments_probability_pair"),
        ),
        sa.CheckConstraint(
            "recommendation IS NULL OR recommendation IN ('approve', 'reject', 'manual_review')",
            name=op.f("ck_application_assessments_recommendation"),
        ),
        sa.CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('low', 'medium', 'high')",
            name=op.f("ck_application_assessments_risk_level"),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')",
            name=op.f("ck_application_assessments_status"),
        ),
        sa.CheckConstraint(
            "attempt_no > 0", name=op.f("ck_application_assessments_positive_attempt")
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_assessments_application_id_applications"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_assessments")),
        sa.UniqueConstraint(
            "application_id",
            "attempt_no",
            name=op.f("uq_application_assessments_application_id"),
        ),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        "ix_application_assessments_status_created",
        "application_assessments",
        ["status", "created_at"],
        unique=False,
    )
    op.create_table(
        "application_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "from_status",
            sa.String(length=30, collation="utf8mb4_bin").with_variant(
                sa.String(length=30, collation="BINARY"), "sqlite"
            ),
            nullable=True,
        ),
        sa.Column(
            "to_status",
            sa.String(length=30, collation="utf8mb4_bin").with_variant(
                sa.String(length=30, collation="BINARY"), "sqlite"
            ),
            nullable=True,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "from_status IS NULL OR from_status IN ('draft', 'submitted', 'in_review', 'approved', 'rejected', 'signed', 'disbursed')",
            name=op.f("ck_application_events_from_status"),
        ),
        sa.CheckConstraint(
            "to_status IS NULL OR to_status IN ('draft', 'submitted', 'in_review', 'approved', 'rejected', 'signed', 'disbursed')",
            name=op.f("ck_application_events_to_status"),
        ),
        sa.CheckConstraint(
            "actor_user_id IS NULL OR actor_user_id > 0",
            name=op.f("ck_application_events_positive_actor"),
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            name=op.f("fk_application_events_application_id_applications"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_application_events")),
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_unicode_ci",
        mysql_engine="InnoDB",
    )
    op.create_index(
        op.f("ix_application_events_actor_user_id"),
        "application_events",
        ["actor_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_application_events_application_order",
        "application_events",
        ["application_id", "id"],
        unique=False,
    )


def downgrade() -> None:
    """Удаляем только собственные таблицы; companies остаётся в ведении Laravel."""
    op.drop_index(
        "ix_application_events_application_order", table_name="application_events"
    )
    op.drop_index(
        op.f("ix_application_events_actor_user_id"), table_name="application_events"
    )
    op.drop_table("application_events")
    op.drop_index(
        "ix_application_assessments_status_created",
        table_name="application_assessments",
    )
    op.drop_table("application_assessments")
    op.drop_index("ix_applications_status_created", table_name="applications")
    op.drop_index(op.f("ix_applications_product_id"), table_name="applications")
    op.drop_index("ix_applications_company_created", table_name="applications")
    op.drop_index("ix_applications_assignee_status", table_name="applications")
    op.drop_index(op.f("ix_applications_applicant_user_id"), table_name="applications")
    op.drop_table("applications")
    op.drop_index(
        op.f("ix_company_memberships_user_id"), table_name="company_memberships"
    )
    op.drop_table("company_memberships")
    op.drop_table("credit_products")
