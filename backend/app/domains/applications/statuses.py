"""Допустимые значения состояния заявки в базе"""

from enum import StrEnum


class ApplicationStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIGNED = "signed"
    DISBURSED = "disbursed"


STATUS_VALUES_SQL = ", ".join(f"'{status.value}'" for status in ApplicationStatus)
