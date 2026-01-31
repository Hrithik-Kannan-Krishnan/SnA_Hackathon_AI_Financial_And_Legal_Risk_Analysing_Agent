"""
Financial document completeness validation schema.
Separate from legal document validation - focuses on financial statement requirements.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class FinancialDocumentType(str, Enum):
    FINANCIAL_SPREADSHEET = "financial_spreadsheet"
    FINANCIAL_REPORT = "financial_report"

class FinancialStatementType(BaseModel):
    profit_and_loss_present: bool = False
    balance_sheet_present: bool = False
    cash_flow_present: bool = False
    notes_present: bool = False

class PerformanceMetrics(BaseModel):
    sales_revenue_present: bool = False
    expenses_present: bool = False
    net_profit_present: bool = False
    eps_present: bool = False
    ebitda_present: bool = False
    
    @property
    def performance_items_count(self) -> int:
        """Count of performance metrics found"""
        return sum([
            self.sales_revenue_present,
            self.expenses_present,
            self.net_profit_present,
            self.eps_present,
            self.ebitda_present,
        ])

class PeriodEvidence(BaseModel):
    fy_ending_present: bool = False
    quarterly_dates_present: bool = False
    monthly_periods_present: bool = False
    year_references_present: bool = False
    
    @property
    def has_period_evidence(self) -> bool:
        """Check if any period evidence is present"""
        return any([
            self.fy_ending_present,
            self.quarterly_dates_present,
            self.monthly_periods_present,
            self.year_references_present,
        ])

class NumericEvidence(BaseModel):
    substantial_numbers_present: bool = False
    currency_amounts_present: bool = False
    percentages_present: bool = False
    ratios_present: bool = False
    
    @property
    def numeric_content_score(self) -> int:
        """Score numeric content richness (0-20 points)"""
        score = 0
        if self.substantial_numbers_present:
            score += 8
        if self.currency_amounts_present:
            score += 5
        if self.percentages_present:
            score += 4
        if self.ratios_present:
            score += 3
        return min(score, 20)

class FinancialCompletenessScores(BaseModel):
    financial_statements_score: int = Field(default=0, ge=0, le=30, description="Score for having core financial statements")
    performance_metrics_score: int = Field(default=0, ge=0, le=25, description="Score for having performance metrics")
    period_evidence_score: int = Field(default=0, ge=0, le=25, description="Score for having period/date evidence")
    numeric_content_score: int = Field(default=0, ge=0, le=20, description="Score for numeric content richness")
    overall_score: int = Field(default=0, ge=0, le=100, description="Total completeness score")
    classification: str = Field(default="reject_incomplete", description="accept_ok, accept_with_warnings, or reject_incomplete")

class FinancialCompletenessFlags(BaseModel):
    no_financial_statements: bool = False
    insufficient_performance_metrics: bool = False
    missing_period_evidence: bool = False
    minimal_numeric_content: bool = False
    likely_cover_page_only: bool = False
    likely_notes_only: bool = False

class FinancialCompletenessAnalysis(BaseModel):
    """Analysis results for financial document completeness"""
    document_type: FinancialDocumentType
    financial_statements: FinancialStatementType
    performance_metrics: PerformanceMetrics
    period_evidence: PeriodEvidence
    numeric_evidence: NumericEvidence
    scores: FinancialCompletenessScores
    flags: FinancialCompletenessFlags
