"""Настройки таблиц и поля времени; часовой пояс БД должен быть UTC."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

ACTIVE_TYPE = Boolean(create_constraint=True, name="is_active")
TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def code_type(length: int) -> String:
    return String(length, collation="utf8mb4_bin").with_variant(
        String(length, collation="BINARY"), "sqlite"
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
