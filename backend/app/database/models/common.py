from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from sqlalchemy.orm import Mapped, mapped_column

ID_TYPE = BIGINT(unsigned=True).with_variant(Integer(), "sqlite")
DATETIME_TYPE = DATETIME(fsp=6).with_variant(DateTime(), "sqlite")
ACTIVE_TYPE = Boolean(create_constraint=True, name="is_active")
TABLE_OPTIONS = {
    "mysql_engine": "InnoDB",
    "mysql_charset": "utf8mb4",
    "mysql_collate": "utf8mb4_unicode_ci",
}


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def code_type(length: int) -> String:
    return String(length, collation="utf8mb4_bin").with_variant(
        String(length, collation="BINARY"), "sqlite"
    )


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DATETIME_TYPE, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME_TYPE, default=utcnow, onupdate=utcnow
    )
