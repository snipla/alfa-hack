from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreditScoringFeatures(BaseModel):
    """Input features expected by the CatBoost credit scoring model."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    loan_term_months: int = Field(..., gt=0, description="Loan term in months")
    employees_count: float = Field(
        ...,
        ge=0.0,
        description="Employees count (raw count or log1p-transformed if log_transformed=True)",
    )
    business_type: str | int = Field(..., description="Business type (1 - legal entity, 2 - IE)")
    is_rev_line_of_loan: str | int | bool = Field(
        ..., description="Revolving line of credit flag (0/1)"
    )
    loan_amount_rub: float = Field(
        ...,
        gt=0.0,
        description="Loan amount in RUB (raw amount or log1p-transformed if log_transformed=True)",
    )
    is_franchise: str | int | bool = Field(..., description="Franchise flag (0/1)")
    industry_sector: str = Field(..., description="Two-digit industry code or 'unknown'")
    business_age_months: int = Field(..., ge=0, description="Business age in months")
    okved_risk_level: str | int = Field(..., description="OKVED risk category (1, 2, or 3)")
    authorized_capital: float = Field(..., ge=0.0, description="Authorized capital in RUB")
    revenue_last_year: float = Field(..., ge=0.0, description="Revenue for the last year in RUB")
    revenue_growth_rate: float = Field(..., description="Revenue growth rate in percent")
    net_profit: float = Field(..., description="Net profit in RUB")
    has_tax_arrears: str | int | bool = Field(..., description="Tax arrears flag (0/1)")
    has_blocked_accounts: str | int | bool = Field(..., description="Blocked accounts flag (0/1)")
    bki_score: int = Field(..., ge=0, le=1000, description="Credit bureau score (300-850)")
    current_debt_load: float = Field(..., ge=0.0, description="Current debt load in RUB")
    max_delinquency_days: int = Field(..., ge=0, description="Maximum delinquency in days")
    active_credits_count: int = Field(..., ge=0, description="Number of active credits")
    fssp_debt_amount: float = Field(..., ge=0.0, description="FSSP debt amount in RUB")
    active_lawsuits_count: int = Field(..., ge=0, description="Number of active lawsuits")
    loan_purpose: str = Field(..., description="Purpose of the loan")
    ownership_structure: str = Field(..., description="Ownership structure")
    business_scale: str = Field(..., description="Business scale category")

    def to_feature_dict(self) -> dict[str, Any]:
        return self.model_dump()


class PredictionResult(BaseModel):
    """Single prediction output from CatBoostClassifier."""

    model_config = ConfigDict(frozen=True)

    prediction: int = Field(..., description="Predicted class (1 - approved/repaid, 0 - default)")
    approval_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of class 1 (loan repaid)"
    )
    default_probability: float = Field(
        ..., ge=0.0, le=1.0, description="Probability of class 0 (default)"
    )
