from __future__ import annotations

from typing import List, Literal, Dict, Any, Tuple
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    doc_type_guess: Literal["spa", "apa", "msa", "loi", "term_sheet", "nda", "teaser", "financials", "other"]
    language: str = "en"
    page_count: int = 0
    source: Literal["pdf", "docx", "txt", "scanned_pdf"]
    ocr_used: bool = False

class EntityInfo(BaseModel):
    name: str = ""
    aliases: List[str] = Field(default_factory=list)
    jurisdiction: str = ""
    entity_type: Literal["company", "individual", "fund", "other"] = "company"

class Entities(BaseModel):
    buyer: EntityInfo = Field(default_factory=EntityInfo)
    seller: EntityInfo = Field(default_factory=EntityInfo)
    target: EntityInfo = Field(default_factory=EntityInfo)

class DealInfo(BaseModel):
    structure: Literal["asset_purchase", "share_purchase", "merger", "scheme", "tender_offer", "unknown"] = "unknown"
    signing_date: str = ""
    closing_date: str = ""
    effective_date: str = ""
    governing_law: str = ""
    venue_forum: str = ""
    defined_terms_present: bool = False
    schedule_or_exhibit_refs_present: bool = False

class PriceAndPayment(BaseModel):
    purchase_price_present: bool = False
    currency_present: bool = False
    enterprise_value_present: bool = False
    equity_value_present: bool = False
    net_debt_present: bool = False
    working_capital_present: bool = False
    adjustment_mechanism_present: bool = False
    earnout_present: bool = False
    escrow_holdback_present: bool = False
    payment_form: Literal["cash", "stock", "mixed", "unknown"] = "unknown"
    evidence_snippets: List[str] = Field(default_factory=list)

class RepTopics(BaseModel):
    authority_organisation: bool = False
    capitalisation: bool = False
    financial_statements: bool = False
    undisclosed_liabilities: bool = False
    compliance_with_laws: bool = False
    tax: bool = False
    employment_benefits: bool = False
    ip: bool = False
    material_contracts: bool = False
    litigation_investigations: bool = False
    environmental: bool = False
    anti_corruption_sanctions_aml: bool = False
    data_protection_privacy: bool = False

class RepsAndWarranties(BaseModel):
    section_present: bool = False
    disclosure_schedules_present: bool = False
    mae_mac_present: bool = False
    knowledge_qualifiers_present: bool = False
    rep_topics_hit: RepTopics = Field(default_factory=RepTopics)
    evidence_snippets: List[str] = Field(default_factory=list)

class Covenants(BaseModel):
    section_present: bool = False
    ordinary_course_present: bool = False
    negative_covenants_present: bool = False
    access_to_info_due_diligence_present: bool = False
    employee_matters_present: bool = False
    confidentiality_noncompete_present: bool = False
    tsa_transition_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class ClosingConditions(BaseModel):
    section_present: bool = False
    regulatory_approvals_present: bool = False
    third_party_consents_present: bool = False
    shareholder_board_approval_present: bool = False
    no_injunction_present: bool = False
    bring_down_present: bool = False
    deliverables_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class TerminationAndRemedies(BaseModel):
    termination_rights_present: bool = False
    outside_date_present: bool = False
    break_fee_present: bool = False
    specific_performance_present: bool = False
    remedies_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class IndemnitiesAndLimits(BaseModel):
    indemnity_present: bool = False
    survival_present: bool = False
    basket_present: bool = False
    cap_present: bool = False
    escrow_claims_process_present: bool = False
    fraud_carveout_present: bool = False
    rwi_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class Financials(BaseModel):
    financial_statements_present: bool = False
    audited_unaudited_present: bool = False
    standard_present: Literal["ifrs", "us_gaap", "ssfrs", "other", "unknown"] = "unknown"
    period_covered_present: bool = False
    ebitda_present: bool = False
    revenue_recognition_present: bool = False
    forecast_budget_present: bool = False
    qoe_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class CapitalAndDebt(BaseModel):
    cap_table_present: bool = False
    securities_present: bool = False
    debt_facility_present: bool = False
    liens_security_interest_present: bool = False
    defaults_waivers_present: bool = False
    payoff_release_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class Tax(BaseModel):
    tax_returns_present: bool = False
    tax_audits_disputes_present: bool = False
    withholding_present: bool = False
    vat_gst_present: bool = False
    transfer_pricing_present: bool = False
    tax_indemnity_covenant_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class LitigationAndAllegations(BaseModel):
    litigation_present: bool = False
    allegations_accusations_present: bool = False
    regulatory_investigation_present: bool = False
    demand_letters_present: bool = False
    settlement_consent_order_present: bool = False
    contingent_liability_reserves_present: bool = False
    whistleblower_internal_investigation_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class Compliance(BaseModel):
    anti_bribery_present: bool = False
    aml_kyc_sanctions_present: bool = False
    competition_antitrust_present: bool = False
    privacy_data_protection_present: bool = False
    cybersecurity_breach_present: bool = False
    export_controls_present: bool = False
    environment_hs_present: bool = False
    evidence_snippets: List[str] = Field(default_factory=list)

class EvidenceStrength(BaseModel):
    numbers_present: bool = False
    dates_present: bool = False
    percentages_present: bool = False
    defined_term_pattern_present: bool = False
    schedule_exhibit_pattern_present: bool = False

class Scores(BaseModel):
    bucket_coverage_score: int = 0
    evidence_strength_score: int = 0
    overall_score: int = 0
    classification: Literal["reject_incomplete", "accept_with_warnings", "accept_ok"] = "reject_incomplete"

class Flags(BaseModel):
    likely_teaser_or_summary: bool = False
    missing_core_buckets: List[str] = Field(default_factory=list)
    generic_language_without_details: bool = False
    unsupported_no_litigation_claim: bool = False

class DealCompletenessAnalysis(BaseModel):
    """
    Comprehensive deal document analysis schema with completeness validation.
    Implements minimum bucket coverage rules to prevent bypass attempts.
    """
    doc_meta: DocumentMetadata
    entities: Entities = Field(default_factory=Entities)
    deal: DealInfo = Field(default_factory=DealInfo)
    price_and_payment: PriceAndPayment = Field(default_factory=PriceAndPayment)
    reps_and_warranties: RepsAndWarranties = Field(default_factory=RepsAndWarranties)
    covenants: Covenants = Field(default_factory=Covenants)
    closing_conditions: ClosingConditions = Field(default_factory=ClosingConditions)
    termination_and_remedies: TerminationAndRemedies = Field(default_factory=TerminationAndRemedies)
    indemnities_and_limits: IndemnitiesAndLimits = Field(default_factory=IndemnitiesAndLimits)
    financials: Financials = Field(default_factory=Financials)
    capital_and_debt: CapitalAndDebt = Field(default_factory=CapitalAndDebt)
    tax: Tax = Field(default_factory=Tax)
    litigation_and_allegations: LitigationAndAllegations = Field(default_factory=LitigationAndAllegations)
    compliance: Compliance = Field(default_factory=Compliance)
    evidence_strength: EvidenceStrength = Field(default_factory=EvidenceStrength)
    scores: Scores = Field(default_factory=Scores)
    flags: Flags = Field(default_factory=Flags)

    def calculate_bucket_coverage(self) -> int:
        """Calculate bucket coverage score (0-70 points) using 7 core buckets."""
        
        # Define core buckets with minimum hit requirements
        core_buckets = [
            # Bucket A: Deal identity (2+ hits required)
            self._bucket_a_deal_identity(),
            
            # Bucket B: Price/payment (2+ hits required)  
            self._bucket_b_price_payment(),
            
            # Bucket C: Reps & warranties (2+ hits required)
            self._bucket_c_reps_warranties(),
            
            # Bucket E: Closing conditions (2+ hits required)
            self._bucket_e_closing_conditions(),
            
            # Bucket G: Indemnities & limits (2+ hits required)
            self._bucket_g_indemnities_limits(),
            
            # Bucket H: Financials (2+ hits required)
            self._bucket_h_financials(),
            
            # Bucket K: Litigation/allegations (2+ hits required)
            self._bucket_k_litigation_allegations()
        ]
        
        # Each bucket present = 10 points, max = 70
        return sum(core_buckets) * 10

    def _bucket_a_deal_identity(self) -> bool:
        """Bucket A: Deal identity - needs 2+ hits"""
        hits = [
            bool(self.entities.buyer.name),
            bool(self.entities.seller.name), 
            bool(self.entities.target.name),
            self.deal.structure != "unknown",
            bool(self.deal.signing_date or self.deal.closing_date or self.deal.effective_date),
            bool(self.deal.governing_law),
            self.deal.defined_terms_present
        ]
        return sum(hits) >= 2

    def _bucket_b_price_payment(self) -> bool:
        """Bucket B: Price/payment - needs 2+ hits"""
        hits = [
            self.price_and_payment.purchase_price_present,
            self.price_and_payment.currency_present,
            self.price_and_payment.enterprise_value_present,
            self.price_and_payment.equity_value_present,
            self.price_and_payment.adjustment_mechanism_present,
            self.price_and_payment.earnout_present,
            self.price_and_payment.escrow_holdback_present,
            self.price_and_payment.payment_form != "unknown"
        ]
        return sum(hits) >= 2

    def _bucket_c_reps_warranties(self) -> bool:
        """Bucket C: Reps & warranties - needs 2+ hits"""
        rep_topic_hits = sum([
            self.reps_and_warranties.rep_topics_hit.authority_organisation,
            self.reps_and_warranties.rep_topics_hit.financial_statements,
            self.reps_and_warranties.rep_topics_hit.litigation_investigations,
            self.reps_and_warranties.rep_topics_hit.compliance_with_laws,
            self.reps_and_warranties.rep_topics_hit.material_contracts,
            self.reps_and_warranties.rep_topics_hit.tax,
            self.reps_and_warranties.rep_topics_hit.employment_benefits
        ])
        
        hits = [
            self.reps_and_warranties.section_present,
            self.reps_and_warranties.disclosure_schedules_present,
            self.reps_and_warranties.mae_mac_present,
            self.reps_and_warranties.knowledge_qualifiers_present,
            rep_topic_hits >= 3  # Multiple rep topics count as 1 hit
        ]
        return sum(hits) >= 2

    def _bucket_e_closing_conditions(self) -> bool:
        """Bucket E: Closing conditions - needs 2+ hits"""
        hits = [
            self.closing_conditions.section_present,
            self.closing_conditions.regulatory_approvals_present,
            self.closing_conditions.third_party_consents_present,
            self.closing_conditions.shareholder_board_approval_present,
            self.closing_conditions.bring_down_present,
            self.closing_conditions.deliverables_present,
            self.closing_conditions.no_injunction_present
        ]
        return sum(hits) >= 2

    def _bucket_g_indemnities_limits(self) -> bool:
        """Bucket G: Indemnities & limits - needs 2+ hits"""
        hits = [
            self.indemnities_and_limits.indemnity_present,
            self.indemnities_and_limits.survival_present,
            self.indemnities_and_limits.basket_present,
            self.indemnities_and_limits.cap_present,
            self.indemnities_and_limits.fraud_carveout_present,
            self.indemnities_and_limits.escrow_claims_process_present,
            self.indemnities_and_limits.rwi_present
        ]
        return sum(hits) >= 2

    def _bucket_h_financials(self) -> bool:
        """Bucket H: Financials - needs 2+ hits"""
        hits = [
            self.financials.financial_statements_present,
            self.financials.audited_unaudited_present,
            self.financials.ebitda_present,
            self.financials.revenue_recognition_present,
            self.financials.forecast_budget_present,
            self.financials.qoe_present,
            self.capital_and_debt.cap_table_present,
            self.capital_and_debt.debt_facility_present
        ]
        return sum(hits) >= 2

    def _bucket_k_litigation_allegations(self) -> bool:
        """Bucket K: Litigation/allegations - needs 2+ hits"""
        hits = [
            self.litigation_and_allegations.litigation_present,
            self.litigation_and_allegations.allegations_accusations_present,
            self.litigation_and_allegations.regulatory_investigation_present,
            self.litigation_and_allegations.settlement_consent_order_present,
            self.litigation_and_allegations.whistleblower_internal_investigation_present,
            self.compliance.anti_bribery_present,
            self.compliance.aml_kyc_sanctions_present,
            self.compliance.competition_antitrust_present
        ]
        return sum(hits) >= 2

    def calculate_evidence_strength(self) -> int:
        """Calculate evidence strength score (0-30 points) based on hard-to-fake details."""
        score = 0
        
        # Currency or price-format present = +6
        if self.price_and_payment.currency_present or self.evidence_strength.numbers_present:
            score += 6
            
        # Dates present = +6  
        if (self.evidence_strength.dates_present or 
            bool(self.deal.signing_date or self.deal.closing_date or self.deal.effective_date)):
            score += 6
            
        # Percentages present = +4
        if self.evidence_strength.percentages_present:
            score += 4
            
        # Defined-term pattern present = +7
        if self.evidence_strength.defined_term_pattern_present or self.deal.defined_terms_present:
            score += 7
            
        # Schedule/exhibit pattern present = +7
        if self.evidence_strength.schedule_exhibit_pattern_present or self.deal.schedule_or_exhibit_refs_present:
            score += 7
            
        return min(score, 30)  # Max = 30
            
    def check_hard_fail_rules(self) -> Tuple[bool, str]:
        """Check hard fail (instant reject) rules that bypass normal scoring."""
        
        # Rule 1: No parties - at least 2 of 3 party names must be present
        parties_present = sum([
            bool(self.entities.buyer.name),
            bool(self.entities.seller.name), 
            bool(self.entities.target.name)
        ])
        if parties_present < 2:
            return True, "No parties: Buyer/seller/target names not found (at least 2 of 3 missing)"
            
        # Rule 2: No transaction structure
        if self.deal.structure == "unknown":
            return True, "No transaction structure: No 'asset purchase/share purchase/merger/acquisition' style hits"
            
        # Rule 3: Generic-only indicator (high narrative but missing hard evidence)
        has_hard_evidence = any([
            self.evidence_strength.numbers_present,
            self.evidence_strength.dates_present,
            self.evidence_strength.schedule_exhibit_pattern_present,
            self.evidence_strength.defined_term_pattern_present
        ])
        
        # Check if document is long but lacks hard evidence (likely marketing material)
        if (not has_hard_evidence and 
            self.scores.bucket_coverage_score < 30 and  # Less than 3 core buckets
            self.doc_meta.doc_type_guess in ["teaser", "other"]):
            return True, "Generic-only indicator: High narrative keywords but missing hard evidence"
            
        # Rule 4: Unsupported "no litigation" claim
        if (self.flags.unsupported_no_litigation_claim and
            not self.deal.schedule_or_exhibit_refs_present and
            not self.reps_and_warranties.disclosure_schedules_present):
            return True, "Unsupported 'no litigation' claim without schedule references"
            
        return False, ""

    def detect_teaser_or_loi(self) -> bool:
        """Detect if document is likely a teaser or LOI (soft flag)."""
        
        # Check for teaser/LOI keywords
        is_teaser_type = self.doc_meta.doc_type_guess in ["teaser", "loi", "term_sheet", "other"]
        
        # Missing critical sections (Indemnities AND (Closing conditions OR Reps))
        missing_indemnities = not self._bucket_g_indemnities_limits()
        missing_closing_or_reps = (not self._bucket_e_closing_conditions() or 
                                  not self._bucket_c_reps_warranties())
        
        return is_teaser_type and missing_indemnities and missing_closing_or_reps

    def validate_completeness(self) -> None:
        """Apply completeness rules with precise 0-100 scoring and hard fail rules."""
        
        # Check hard fail rules first (instant reject regardless of score)
        hard_fail, hard_fail_reason = self.check_hard_fail_rules()
        if hard_fail:
            self.scores.bucket_coverage_score = 0
            self.scores.evidence_strength_score = 0
            self.scores.overall_score = 0
            self.scores.classification = "reject_incomplete"
            self.flags.likely_teaser_or_summary = True
            self.flags.missing_core_buckets = ["HARD_FAIL: " + hard_fail_reason]
            return
        
        # Calculate scores (0-100 scale)
        self.scores.bucket_coverage_score = self.calculate_bucket_coverage()  # 0-70
        self.scores.evidence_strength_score = self.calculate_evidence_strength()  # 0-30
        self.scores.overall_score = self.scores.bucket_coverage_score + self.scores.evidence_strength_score  # 0-100

        # Identify missing core buckets for reporting
        bucket_names = [
            "deal_identity", "price_payment", "reps_warranties", 
            "closing_conditions", "indemnities_limits", 
            "financials", "litigation_claims"
        ]
        
        bucket_results = [
            self._bucket_a_deal_identity(),
            self._bucket_b_price_payment(),
            self._bucket_c_reps_warranties(),
            self._bucket_e_closing_conditions(),
            self._bucket_g_indemnities_limits(),
            self._bucket_h_financials(),
            self._bucket_k_litigation_allegations()
        ]
        
        self.flags.missing_core_buckets = [
            bucket_names[i] for i, present in enumerate(bucket_results) if not present
        ]

        # Apply scoring-based classification rules
        if self.scores.overall_score < 50:
            # 0-49 → reject_incomplete
            self.scores.classification = "reject_incomplete"
        elif self.scores.overall_score < 70:
            # 50-69 → accept_with_warnings  
            self.scores.classification = "accept_with_warnings"
        else:
            # 70-100 → accept_ok
            self.scores.classification = "accept_ok"
        
        # Check for teaser/LOI detection (soft flag)
        self.flags.likely_teaser_or_summary = self.detect_teaser_or_loi()
        
        # If likely teaser, force accept_with_warnings at best
        if self.flags.likely_teaser_or_summary and self.scores.classification == "accept_ok":
            self.scores.classification = "accept_with_warnings"

        # Check for additional red flags
        if (not self.evidence_strength.numbers_present and 
            not self.evidence_strength.dates_present and 
            not self.evidence_strength.schedule_exhibit_pattern_present and
            not self.evidence_strength.defined_term_pattern_present and
            self.scores.bucket_coverage_score > 0):
            self.flags.generic_language_without_details = True

        if (not self.litigation_and_allegations.litigation_present and 
            not self.deal.schedule_or_exhibit_refs_present and
            not self.reps_and_warranties.disclosure_schedules_present):
            self.flags.unsupported_no_litigation_claim = True
