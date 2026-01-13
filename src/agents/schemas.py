from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field

DocType = Literal["financial", "contract", "hr_policy", "other"]

class RouterDecision(BaseModel):
    doc_type: DocType
    rationale: str

class Evidence(BaseModel):
    label: str = Field(..., description="What this evidence supports, e.g., change_of_control, indemnity_cap")
    snippet: str = Field(..., description="A short excerpt copied from the text (<= 30 words)")
    note: str = Field(..., description="Why it matters")

class LegalRiskFinding(BaseModel):
    risk_level: Literal["Low", "Medium", "High"]
    red_flags: List[str] = Field(default_factory=list)
    clauses: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    rationale: str

class FinancialAnomalyFinding(BaseModel):
    anomalies: List[str] = Field(default_factory=list)
    key_metrics: List[str] = Field(default_factory=list)
    rationale: str
