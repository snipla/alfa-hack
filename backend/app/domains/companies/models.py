"""Компании и доступ к ним по внешним идентификаторам Laravel"""

from datetime import date, datetime
from typing import Any, ClassVar

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.database.models.base import Base
from app.database.models.common import (
    ACTIVE_TYPE,
    TABLE_OPTIONS,
    Timestamps,
    # code_type,  # Нужен только закомментированной старой схеме Company.
)

# Предыдущая схема Python backend отключена: companies принадлежит Laravel

# class Company(Timestamps, Base):
#     __tablename__ = "companies"
#     __table_args__ = (
#         CheckConstraint(
#             "legal_form IN ('legal_entity', 'individual_entrepreneur')",
#             name="legal_form",
#         ),
#         CheckConstraint(
#             "(legal_form = 'legal_entity' AND length(inn) = 10 "
#             "AND inn REGEXP '^[0-9]{10}$') OR "
#             "(legal_form = 'individual_entrepreneur' AND length(inn) = 12 "
#             "AND inn REGEXP '^[0-9]{12}$')",
#             name="inn_format",
#         ),
#         CheckConstraint(
#             "ogrn IS NULL OR "
#             "(legal_form = 'legal_entity' AND length(ogrn) = 13 "
#             "AND ogrn REGEXP '^[0-9]{13}$') OR "
#             "(legal_form = 'individual_entrepreneur' AND length(ogrn) = 15 "
#             "AND ogrn REGEXP '^[0-9]{15}$')",
#             name="ogrn_format",
#         ),
#         TABLE_OPTIONS,
#     )
#
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     inn: Mapped[str] = mapped_column(String(12), unique=True)
#     name: Mapped[str] = mapped_column(String(255))
#     legal_form: Mapped[str] = mapped_column(code_type(30))
#     ogrn: Mapped[str | None] = mapped_column(String(15), unique=True)
#     registration_date: Mapped[date | None] = mapped_column(Date)
#     okved_code: Mapped[str | None] = mapped_column(String(20))
#     is_active: Mapped[bool] = mapped_column(
#         ACTIVE_TYPE, default=True, server_default=text("1")
#     )


class Company(Base):
    """Отображение существующей таблицы Laravel; Alembic ею не управляет.

    Источник схемы: frontend/database/migrations/
    2026_10_14_195621_create_companies_table.php.
    Создание и изменение компаний выполняются в Laravel.
    """

    __tablename__ = "companies"
    __table_args__: ClassVar[dict[str, Any]] = {"info": {"managed_by": "laravel"}}

    # SQLite-вариант используется только для изолированных тестов.
    id: Mapped[int] = mapped_column(
        BIGINT(unsigned=True).with_variant(Integer(), "sqlite"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(255))
    inn: Mapped[int] = mapped_column(Integer)
    ogrn: Mapped[int] = mapped_column(Integer)
    registration_date: Mapped[date] = mapped_column(Date)
    # Laravel timestamps() допускает NULL; Python не назначает свои defaults.
    created_at: Mapped[datetime | None] = mapped_column(DateTime)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime)


class CompanyMembership(Timestamps, Base):
    __tablename__ = "company_memberships"

    __table_args__ = (
        CheckConstraint("user_id > 0", name="positive_user_id"),
        TABLE_OPTIONS,
    )

    company_id: Mapped[int] = mapped_column(
        # Integer,  # Не совпадает с BIGINT UNSIGNED companies.id из Laravel.
        BIGINT(unsigned=True).with_variant(Integer(), "sqlite"),
        ForeignKey("companies.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    is_active: Mapped[bool] = mapped_column(
        ACTIVE_TYPE, default=True, server_default=text("1")
    )
