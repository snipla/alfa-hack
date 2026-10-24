from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.common import (
    DATETIME_TYPE,
    ID_TYPE,
    TABLE_OPTIONS,
    Timestamps,
    code_type,
)


class ApplicationAssessment(Timestamps, Base):
    __tablename__ = "application_assessments"
    __table_args__ = (
        UniqueConstraint("application_id", "attempt_no"),
        CheckConstraint("attempt_no > 0", name="positive_attempt"),
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed')", name="status"
        ),
        CheckConstraint(
            "(probability_value IS NULL AND probability_kind IS NULL) OR "
            "(probability_value IS NOT NULL AND probability_value BETWEEN 0 AND 1 "
            "AND probability_kind IS NOT NULL AND probability_kind IN "
            "('default_probability', 'approval_probability'))",
            name="probability_pair",
        ),
        CheckConstraint(
            "risk_level IS NULL OR risk_level IN ('low', 'medium', 'high')",
            name="risk_level",
        ),
        CheckConstraint(
            "recommendation IS NULL OR recommendation IN "
            "('approve', 'reject', 'manual_review')",
            name="recommendation",
        ),
        Index("ix_application_assessments_status_created", "status", "created_at"),
        TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    application_id: Mapped[int] = mapped_column(
        ID_TYPE, ForeignKey("applications.id", ondelete="RESTRICT")
    )
    attempt_no: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        code_type(20), default="queued", server_default=text("'queued'")
    )
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100))
    feature_schema_version: Mapped[str | None] = mapped_column(String(50))
    # Сохраняем исходные сведения и точный вход модели, не обучающую метку.
    source_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    features_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    result_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    probability_value: Mapped[Decimal | None] = mapped_column(Numeric(7, 6))
    probability_kind: Mapped[str | None] = mapped_column(code_type(30))
    risk_level: Mapped[str | None] = mapped_column(code_type(20))
    recommendation: Mapped[str | None] = mapped_column(code_type(30))
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    error_code: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime | None] = mapped_column(DATETIME_TYPE)
    completed_at: Mapped[datetime | None] = mapped_column(DATETIME_TYPE)
