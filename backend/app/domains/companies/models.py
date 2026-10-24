"""Компании и доступ к ним по внешним идентификаторам Laravel"""

from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.common import (
    ACTIVE_TYPE,
    ID_TYPE,
    TABLE_OPTIONS,
    Timestamps,
    code_type,
)


class Company(Timestamps, Base):
    __tablename__ = "companies"
    __table_args__ = (
        CheckConstraint(
            "legal_form IN ('legal_entity', 'individual_entrepreneur')",
            name="legal_form",
        ),
        CheckConstraint(
            "(legal_form = 'legal_entity' AND length(inn) = 10 "
            "AND inn REGEXP '^[0-9]{10}$') OR "
            "(legal_form = 'individual_entrepreneur' AND length(inn) = 12 "
            "AND inn REGEXP '^[0-9]{12}$')",
            name="inn_format",
        ),
        CheckConstraint(
            "ogrn IS NULL OR "
            "(legal_form = 'legal_entity' AND length(ogrn) = 13 "
            "AND ogrn REGEXP '^[0-9]{13}$') OR "
            "(legal_form = 'individual_entrepreneur' AND length(ogrn) = 15 "
            "AND ogrn REGEXP '^[0-9]{15}$')",
            name="ogrn_format",
        ),
        TABLE_OPTIONS,
    )

    id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, autoincrement=True)
    inn: Mapped[str] = mapped_column(String(12), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    legal_form: Mapped[str] = mapped_column(code_type(30))
    ogrn: Mapped[str | None] = mapped_column(String(15), unique=True)
    registration_date: Mapped[date | None] = mapped_column(Date)
    okved_code: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(
        ACTIVE_TYPE, default=True, server_default=text("1")
    )


class CompanyMembership(Timestamps, Base):
    __tablename__ = "company_memberships"

    __table_args__ = (
        CheckConstraint("user_id > 0", name="positive_user_id"),
        TABLE_OPTIONS,
    )

    company_id: Mapped[int] = mapped_column(
        ID_TYPE,
        ForeignKey("companies.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(ID_TYPE, primary_key=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        ACTIVE_TYPE, default=True, server_default=text("1")
    )
