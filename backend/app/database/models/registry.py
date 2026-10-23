from app.database.models.base import Base
from app.domains.applications.models import Application, ApplicationEvent
from app.domains.companies.models import Company, CompanyMembership
from app.domains.products.models import CreditProduct
from app.domains.scoring.models import ApplicationAssessment

MANAGED_TABLES = frozenset(
    {
        "companies",
        "company_memberships",
        "credit_products",
        "applications",
        "application_assessments",
        "application_events",
    }
)


def include_model_object(obj, name, type_, reflected, compare_to) -> bool:
    if type_ == "table":
        return name in MANAGED_TABLES
    return True


__all__ = [
    "MANAGED_TABLES",
    "Application",
    "ApplicationAssessment",
    "ApplicationEvent",
    "Base",
    "Company",
    "CompanyMembership",
    "CreditProduct",
    "include_model_object",
]
