"""Заявки и история действий; проверки прав остаются задачей сервисов"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.common import (
    TABLE_OPTIONS,
    Timestamps,
    code_type,
)
from app.domains.applications.enums import STATUS_VALUES_SQL, ApplicationStatus


class Application(Timestamps, Base):
    __tablename__ = "applications"
    __table_args__ = (
        ForeignKeyConstraint(
            ["company_id", "applicant_user_id"],
            ["company_memberships.company_id", "company_memberships.user_id"],
            ondelete="RESTRICT",
        ),
        CheckConstraint("amount > 0", name="positive_amount"),
        CheckConstraint("term_months > 0", name="positive_term"),
        CheckConstraint("version > 0", name="positive_version"),
        CheckConstraint(
            "assigned_to_user_id IS NULL OR assigned_to_user_id > 0",
            name="positive_assignee",
        ),
        CheckConstraint(
            "length(currency) = 3 AND currency REGEXP '^[A-Z]{3}$'",
            name="currency_format",
        ),
        CheckConstraint(f"status IN ({STATUS_VALUES_SQL})", name="status"),
        CheckConstraint(
            "(consent_version IS NULL AND consented_at IS NULL) OR "
            "(consent_version IS NOT NULL AND consented_at IS NOT NULL)",
            name="consent_pair",
        ),
        Index("ix_applications_company_created", "company_id", "created_at"),
        Index("ix_applications_status_created", "status", "created_at"),
        Index("ix_applications_assignee_status", "assigned_to_user_id", "status"),
        TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # company_id: Mapped[int] = mapped_column(Integer)  # Старый тип не совпадает с Laravel.
    company_id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True).with_variant(Integer(), "sqlite")
    )
    applicant_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("credit_products.id", ondelete="RESTRICT"), index=True
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(BigInteger)
    purpose: Mapped[str] = mapped_column(String(500))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(
        code_type(3), default="RUB", server_default=text("'RUB'")
    )
    term_months: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        code_type(30),
        default=ApplicationStatus.DRAFT.value,
        server_default=text("'draft'"),
    )

    product_terms_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    consent_version: Mapped[str | None] = mapped_column(String(50))
    consented_at: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime)
    decision_comment: Mapped[str | None] = mapped_column(Text)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime)
    disbursed_at: Mapped[datetime | None] = mapped_column(DateTime)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    __table_args__ = (
        CheckConstraint(
            "actor_user_id IS NULL OR actor_user_id > 0", name="positive_actor"
        ),
        CheckConstraint(
            f"from_status IS NULL OR from_status IN ({STATUS_VALUES_SQL})",
            name="from_status",
        ),
        CheckConstraint(
            f"to_status IS NULL OR to_status IN ({STATUS_VALUES_SQL})",
            name="to_status",
        ),
        Index("ix_application_events_application_order", "application_id", "id"),
        TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id", ondelete="RESTRICT")
    )

    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    from_status: Mapped[str | None] = mapped_column(code_type(30))
    to_status: Mapped[str | None] = mapped_column(code_type(30))
    comment: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
