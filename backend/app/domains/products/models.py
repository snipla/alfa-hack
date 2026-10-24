"""Каталог кредитных продуктов и их условий."""

from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.common import (
    ACTIVE_TYPE,
    ID_TYPE,
    TABLE_OPTIONS,
    Timestamps,
    code_type,
)


class CreditProduct(Timestamps, Base):
    __tablename__ = "credit_products"
    __table_args__ = (
        CheckConstraint(
            "min_amount > 0 AND max_amount >= min_amount", name="amount_range"
        ),
        CheckConstraint(
            "min_term_months > 0 AND max_term_months >= min_term_months",
            name="term_range",
        ),
        CheckConstraint(
            "annual_rate_percent IS NULL OR annual_rate_percent >= 0",
            name="annual_rate",
        ),
        CheckConstraint(
            "length(currency) = 3 AND currency REGEXP '^[A-Z]{3}$'",
            name="currency_format",
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(code_type(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(
        code_type(3), default="RUB", server_default=text("'RUB'")
    )
    min_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    max_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    min_term_months: Mapped[int] = mapped_column(Integer)
    max_term_months: Mapped[int] = mapped_column(Integer)
    # 18.0000 означает 18% годовых, а не долю 0.18.
    annual_rate_percent: Mapped[Decimal | None] = mapped_column(Numeric(7, 4))
    rules_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    rules_version: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(
        ACTIVE_TYPE, default=True, server_default=text("1")
    )
