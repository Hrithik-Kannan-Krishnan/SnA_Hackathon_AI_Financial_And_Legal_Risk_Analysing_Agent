from __future__ import annotations

import re
from typing import Dict, List, Tuple
from src.agents.deal_completeness_schema import (
    DealCompletenessAnalysis, DocumentMetadata, Entities, EntityInfo,
    DealInfo, PriceAndPayment, RepsAndWarranties, RepTopics,
    ClosingConditions, IndemnitiesAndLimits, Financials, 
    LitigationAndAllegations, EvidenceStrength, Covenants,
    CapitalAndDebt, Tax, Compliance
)

class DealCompletenessAnalyzer:
    """
    Analyzes deal documents for completeness using the comprehensive schema.
    Implements bucket coverage rules to prevent bypass attempts.
    """
    
    def __init__(self):
        # Core regex patterns (strong anti-bypass signals)
        self.defined_term_patterns = [
            r'"[A-Za-z0-9 ,.-]{2,40}"\s+(means|shall mean)',
            r'\b(defined terms|definitions)\b'
        ]
        
        self.schedule_patterns = [
            r'\b(schedule|exhibit|annex|appendix)\s+([A-Z]|\d+)(\.\d+)?\b',
            r'\bdisclosure schedule(s)?\b'
        ]
        
        self.currency_patterns = [
            r'\b(USD|SGD|EUR|GBP|INR|AUD|JPY|CNY)\b',
            r'\b(\$|S\$|€|£)\s?\d'
        ]
        
        self.date_patterns = [
            r'\b\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}\b',
            r'\b\d{4}-\d{2}-\d{2}\b'
        ]
        
        self.percentage_patterns = [
            r'\b\d+(\.\d+)?%\b'
        ]
        
        # Comprehensive bucket keyword lists
        self.bucket_keywords = {
            'deal_identity': [
                'buyer', 'purchaser', 'acquirer', 'seller', 'vendor', 'target', 'acquired company',
                'transaction', 'acquisition', 'merger', 'asset purchase', 'share purchase', 
                'stock purchase', 'merger agreement', 'signing date', 'closing date', 
                'effective date', 'governing law', 'jurisdiction', 'venue', 'forum'
            ],
            'price_payment': [
                'purchase price', 'consideration', 'enterprise value', 'equity value',
                'working capital', 'net debt', 'cash-free debt-free', 'adjustment', 'true-up',
                'closing statement', 'earn-out', 'milestone payment', 'escrow', 'holdback',
                'retention amount', 'cash consideration', 'stock consideration', 'exchange ratio'
            ],
            'reps_warranties': [
                'representations and warranties', 'reps and warranties', 'disclosure schedule',
                'disclosure schedules', 'materiality', 'material adverse effect', 'MAE', 'MAC',
                'knowledge qualifier', 'to the knowledge of', 'authority', 'organisation',
                'capitalization', 'financial statements', 'undisclosed liabilities',
                'compliance with laws', 'tax matters', 'employment', 'benefits',
                'intellectual property', 'IP', 'infringement', 'material contracts',
                'litigation', 'investigation', 'environmental', 'anti-corruption',
                'sanctions', 'AML', 'data protection', 'privacy'
            ],
            'covenants': [
                'covenants', 'ordinary course', 'negative covenant', 'access to information',
                'due diligence', 'employee matters', 'retention', 'non-compete', 'non-solicit',
                'confidentiality', 'transition services', 'TSA'
            ],
            'closing_conditions': [
                'conditions to closing', 'closing conditions', 'CPs', 'regulatory approval',
                'clearance', 'third party consent', 'board approval', 'shareholder approval',
                'no injunction', 'bring-down', 'deliverables', 'closing deliverables'
            ],
            'termination_remedies': [
                'termination', 'terminate', 'outside date', 'long stop date', 'drop dead date',
                'break fee', 'reverse break fee', 'specific performance', 'remedies'
            ],
            'indemnities_limits': [
                'indemnification', 'indemnity', 'survival period', 'basket', 'deductible',
                'tipping basket', 'cap', 'limitation of liability', 'escrow claims',
                'fraud carve-out', 'willful misconduct', 'representation and warranty insurance',
                'RWI'
            ],
            'financials': [
                'income statement', 'profit and loss', 'P&L', 'balance sheet', 'cash flow statement',
                'audited', 'unaudited', 'IFRS', 'US GAAP', 'SSFRS', 'EBITDA', 'adjusted EBITDA',
                'revenue recognition', 'forecast', 'projections', 'budget', 'quality of earnings', 'QoE'
            ],
            'capital_debt': [
                'cap table', 'capitalization table', 'options', 'warrants', 'convertibles',
                'SAFE', 'preference shares', 'credit facility', 'loan agreement', 'debt',
                'lien', 'charge', 'pledge', 'security interest', 'mortgage', 'default',
                'covenant breach', 'waiver', 'payoff letter', 'release of liens'
            ],
            'tax': [
                'tax returns', 'tax audit', 'assessment', 'withholding tax', 'VAT', 'GST',
                'transfer pricing', 'tax indemnity', 'tax covenant'
            ],
            'litigation_claims': [
                'litigation', 'lawsuit', 'claim', 'dispute', 'allegation', 'accusations',
                'complaint', 'demand letter', 'cease and desist', 'investigation', 'inquiry',
                'subpoena', 'settlement', 'consent order', 'injunction', 'contingent liability',
                'provision', 'reserve', 'whistleblower', 'internal investigation',
                'arbitration', 'mediation'
            ],
            'compliance': [
                'anti-bribery', 'anti-corruption', 'FCPA', 'UK bribery act', 'AML', 'KYC',
                'sanctions', 'OFAC', 'antitrust', 'competition law', 'PDPA', 'GDPR',
                'data protection', 'privacy', 'cybersecurity', 'data breach', 'export controls',
                'health and safety', 'environmental'
            ]
        }

    def analyze_document(self, filename: str, text: str, page_count: int = 0) -> DealCompletenessAnalysis:
        """Perform comprehensive analysis of a deal document."""
        
        # Initialize the analysis
        analysis = DealCompletenessAnalysis(
            doc_meta=self._analyze_document_metadata(filename, text, page_count)
        )
        
        # Extract entities
        analysis.entities = self._extract_entities(text)
        
        # Analyze deal structure and terms
        analysis.deal = self._analyze_deal_info(text)
        
        # Analyze financial aspects
        analysis.price_and_payment = self._analyze_price_and_payment(text)
        analysis.financials = self._analyze_financials(text)
        
        # Analyze legal aspects
        analysis.reps_and_warranties = self._analyze_reps_warranties(text)
        analysis.closing_conditions = self._analyze_closing_conditions(text)
        analysis.indemnities_and_limits = self._analyze_indemnities(text)
        analysis.litigation_and_allegations = self._analyze_litigation(text)
        
        # Analyze evidence strength
        analysis.evidence_strength = self._analyze_evidence_strength(text)
        
        # Analyze additional buckets for comprehensive coverage
        analysis.covenants = self._analyze_covenants(text)
        analysis.capital_and_debt = self._analyze_capital_debt(text)
        analysis.tax = self._analyze_tax(text)
        analysis.compliance = self._analyze_compliance(text)
        
        # Validate completeness and calculate scores
        analysis.validate_completeness()
        
        return analysis

    def _analyze_document_metadata(self, filename: str, text: str, page_count: int) -> DocumentMetadata:
        """Analyze document metadata and classify document type."""
        
        filename_lower = filename.lower()
        text_lower = text.lower()
        
        # Enhanced document type guessing with teaser/LOI detection
        doc_type_guess = "other"
        
        # Priority order: check for specific document types first
        if any(term in filename_lower or term in text_lower for term in [
            "teaser", "overview", "executive summary", "information memorandum", "cim"
        ]):
            doc_type_guess = "teaser"
        elif any(term in filename_lower or term in text_lower for term in [
            "loi", "letter of intent", "term sheet", "heads of terms", "memorandum of understanding", "mou"
        ]):
            doc_type_guess = "loi"
        elif "term sheet" in filename_lower or "term sheet" in text_lower:
            doc_type_guess = "term_sheet"
        elif any(term in filename_lower for term in ["spa", "sale", "purchase", "agreement"]):
            doc_type_guess = "spa"
        elif any(term in filename_lower for term in ["apa", "asset"]):
            doc_type_guess = "apa"
        elif any(term in filename_lower or term in text_lower for term in ["merger", "scheme of arrangement"]):
            doc_type_guess = "msa"
        elif any(term in filename_lower or term in text_lower for term in ["confidentiality", "non-disclosure", "nda"]):
            doc_type_guess = "nda"
        elif any(term in filename_lower for term in ["financial", "statement", "audit"]):
            doc_type_guess = "financials"
        
        # Determine source type
        source = "pdf"  # Default assumption
        if filename.lower().endswith('.docx'):
            source = "docx"
        elif filename.lower().endswith('.txt'):
            source = "txt"
        
        return DocumentMetadata(
            doc_type_guess=doc_type_guess,
            language="en",
            page_count=page_count,
            source=source,
            ocr_used=False  # Would need to be set externally if OCR was used
        )

    def _extract_entities(self, text: str) -> Entities:
        """Extract buyer, seller, and target entities."""
        # This is a simplified version - in practice, you'd use more sophisticated NER
        
        # Look for common entity patterns
        company_patterns = [
            r'([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Ltd|Corp|Corporation|Limited|Company)\.?)',
            r'([A-Z][a-zA-Z\s&]+(?:Holdings|Group|Partners|Capital|Ventures))',
        ]
        
        entities = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            entities.extend([match.strip() for match in matches])
        
        # Remove duplicates and filter
        unique_entities = list(set([e for e in entities if len(e) > 5]))
        
        buyer = EntityInfo()
        seller = EntityInfo()
        target = EntityInfo()
        
        # Simple heuristic assignment (in practice, you'd use more context)
        if len(unique_entities) >= 1:
            buyer.name = unique_entities[0]
        if len(unique_entities) >= 2:
            seller.name = unique_entities[1]
        if len(unique_entities) >= 3:
            target.name = unique_entities[2]
        
        return Entities(buyer=buyer, seller=seller, target=target)

    def _analyze_deal_info(self, text: str) -> DealInfo:
        """Analyze deal structure and key information using comprehensive keyword matching."""
        text_lower = text.lower()
        
        # Enhanced structure detection using bucket keywords
        structure = "unknown"
        deal_keywords = self.bucket_keywords['deal_identity']
        
        if any(term in text_lower for term in ["asset purchase", "asset sale"]):
            structure = "asset_purchase"
        elif any(term in text_lower for term in ["share purchase", "stock purchase", "equity purchase"]):
            structure = "share_purchase"
        elif "merger" in text_lower:
            structure = "merger"
        elif "scheme of arrangement" in text_lower:
            structure = "scheme"
        elif "tender offer" in text_lower:
            structure = "tender_offer"
        
        # Extract dates using enhanced patterns
        signing_date = self._extract_first_date(text)
        closing_date = ""
        if any(term in text_lower for term in ["closing date", "completion date"]):
            closing_date = self._extract_date_near_term(text, ["closing", "completion"])
        
        # Enhanced governing law detection
        governing_law = ""
        if any(term in text_lower for term in ["governed by", "governing law", "jurisdiction", "venue"]):
            gov_match = re.search(r'governed?\s+by\s+(?:the\s+)?laws?\s+of\s+([A-Za-z\s]+)', text, re.IGNORECASE)
            if gov_match:
                governing_law = gov_match.group(1).strip()
        
        # Enhanced defined terms and schedules detection
        defined_terms_present = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.defined_term_patterns)
        schedule_refs_present = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.schedule_patterns)
        
        return DealInfo(
            structure=structure,
            signing_date=signing_date,
            closing_date=closing_date,
            governing_law=governing_law,
            defined_terms_present=defined_terms_present,
            schedule_or_exhibit_refs_present=schedule_refs_present
        )

    def _analyze_price_and_payment(self, text: str) -> PriceAndPayment:
        """Analyze pricing and payment terms using comprehensive keyword matching."""
        
        # Use bucket keyword matching for more comprehensive detection
        purchase_price_present = self._check_bucket_keywords(text, 'price_payment', min_hits=2)
        currency_present = any(re.search(pattern, text, re.IGNORECASE) for pattern in self.currency_patterns)
        
        text_lower = text.lower()
        
        # Enhanced valuation terms detection
        enterprise_value_present = "enterprise value" in text_lower
        equity_value_present = "equity value" in text_lower
        net_debt_present = any(term in text_lower for term in ["net debt", "cash-free debt-free"])
        working_capital_present = "working capital" in text_lower
        
        # Enhanced adjustment mechanisms
        adjustment_mechanism_present = any(term in text_lower for term in [
            "adjustment", "true-up", "closing statement", "closing adjustment"
        ])
        
        earnout_present = any(term in text_lower for term in ["earn-out", "earnout", "milestone payment"])
        escrow_present = any(term in text_lower for term in ["escrow", "holdback", "retention amount"])
        
        # Enhanced payment form detection
        payment_form = "unknown"
        if any(term in text_lower for term in ["cash consideration", "stock consideration"]):
            if "cash consideration" in text_lower and "stock consideration" in text_lower:
                payment_form = "mixed"
            elif "cash consideration" in text_lower:
                payment_form = "cash"
            elif "stock consideration" in text_lower:
                payment_form = "stock"
        elif "exchange ratio" in text_lower:
            payment_form = "stock"
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'price_payment')
        
        return PriceAndPayment(
            purchase_price_present=purchase_price_present,
            currency_present=currency_present,
            enterprise_value_present=enterprise_value_present,
            equity_value_present=equity_value_present,
            net_debt_present=net_debt_present,
            working_capital_present=working_capital_present,
            adjustment_mechanism_present=adjustment_mechanism_present,
            earnout_present=earnout_present,
            escrow_holdback_present=escrow_present,
            payment_form=payment_form,
            evidence_snippets=evidence_snippets
        )

    def _analyze_reps_warranties(self, text: str) -> RepsAndWarranties:
        """Analyze representations and warranties section using comprehensive keyword matching."""
        
        # Use comprehensive keyword matching
        section_present = self._check_bucket_keywords(text, 'reps_warranties', min_hits=3)
        
        text_lower = text.lower()
        
        # Enhanced detection using bucket keywords
        disclosure_schedules_present = any(term in text_lower for term in ["disclosure schedule", "disclosure schedules"])
        mae_mac_present = any(term in text_lower for term in ["material adverse effect", "MAE", "MAC"])
        knowledge_qualifiers_present = any(term in text_lower for term in ["knowledge qualifier", "to the knowledge of"])
        
        # Comprehensive representation topics using bucket keywords
        rep_topics = RepTopics(
            authority_organisation=any(term in text_lower for term in ["authority", "organisation", "capitalization"]),
            capitalisation="capitalisation" in text_lower or "capitalization" in text_lower,
            financial_statements="financial statements" in text_lower,
            undisclosed_liabilities="undisclosed liabilit" in text_lower,
            compliance_with_laws="compliance with laws" in text_lower,
            tax="tax matters" in text_lower or ("tax" in text_lower and "return" in text_lower),
            employment_benefits=any(term in text_lower for term in ["employment", "benefits"]),
            ip=any(term in text_lower for term in ["intellectual property", "IP", "infringement"]),
            material_contracts="material contracts" in text_lower,
            litigation_investigations=any(term in text_lower for term in ["litigation", "investigation"]),
            environmental="environmental" in text_lower,
            anti_corruption_sanctions_aml=any(term in text_lower for term in ["anti-corruption", "sanctions", "AML"]),
            data_protection_privacy=any(term in text_lower for term in ["data protection", "privacy"])
        )
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'reps_warranties')
        
        return RepsAndWarranties(
            section_present=section_present,
            disclosure_schedules_present=disclosure_schedules_present,
            mae_mac_present=mae_mac_present,
            knowledge_qualifiers_present=knowledge_qualifiers_present,
            rep_topics_hit=rep_topics,
            evidence_snippets=evidence_snippets
        )

    def _analyze_closing_conditions(self, text: str) -> ClosingConditions:
        """Analyze closing conditions using comprehensive keyword matching."""
        
        section_present = self._check_bucket_keywords(text, 'closing_conditions', min_hits=2)
        
        text_lower = text.lower()
        
        # Enhanced detection using bucket keywords
        regulatory_approvals_present = any(term in text_lower for term in ["regulatory approval", "clearance"])
        third_party_consents_present = "third party consent" in text_lower or "third-party consent" in text_lower
        shareholder_board_approval_present = any(term in text_lower for term in ["board approval", "shareholder approval"])
        no_injunction_present = "no injunction" in text_lower
        bring_down_present = "bring-down" in text_lower or "bring down" in text_lower
        deliverables_present = any(term in text_lower for term in ["deliverables", "closing deliverables"])
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'closing_conditions')
        
        return ClosingConditions(
            section_present=section_present,
            regulatory_approvals_present=regulatory_approvals_present,
            third_party_consents_present=third_party_consents_present,
            shareholder_board_approval_present=shareholder_board_approval_present,
            no_injunction_present=no_injunction_present,
            bring_down_present=bring_down_present,
            deliverables_present=deliverables_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_indemnities(self, text: str) -> IndemnitiesAndLimits:
        """Analyze indemnification provisions using comprehensive keyword matching."""
        
        # Use comprehensive bucket keyword matching
        indemnity_present = self._check_bucket_keywords(text, 'indemnities_limits', min_hits=2)
        
        text_lower = text.lower()
        
        # Enhanced detection
        survival_present = "survival period" in text_lower or "survival" in text_lower
        basket_present = any(term in text_lower for term in ["basket", "deductible", "tipping basket"])
        cap_present = any(term in text_lower for term in ["cap", "limitation of liability", "maximum"])
        escrow_claims_process_present = "escrow claims" in text_lower
        fraud_carveout_present = any(term in text_lower for term in ["fraud carve-out", "willful misconduct"])
        rwi_present = any(term in text_lower for term in [
            "representation and warranty insurance", "RWI", "reps and warranties insurance"
        ])
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'indemnities_limits')
        
        return IndemnitiesAndLimits(
            indemnity_present=indemnity_present,
            survival_present=survival_present,
            basket_present=basket_present,
            cap_present=cap_present,
            escrow_claims_process_present=escrow_claims_process_present,
            fraud_carveout_present=fraud_carveout_present,
            rwi_present=rwi_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_financials(self, text: str) -> Financials:
        """Analyze financial statement information using comprehensive keyword matching."""
        
        financial_statements_present = self._check_bucket_keywords(text, 'financials', min_hits=2)
        
        text_lower = text.lower()
        
        # Enhanced financial analysis detection
        audited_unaudited_present = "audited" in text_lower or "unaudited" in text_lower
        standard_present = "unknown"
        if "IFRS" in text_lower:
            standard_present = "ifrs"
        elif "US GAAP" in text_lower:
            standard_present = "us_gaap"
        elif "SSFRS" in text_lower:
            standard_present = "ssfrs"
        elif any(term in text_lower for term in ["accounting standard", "accounting principle"]):
            standard_present = "other"
        
        period_covered_present = any(term in text_lower for term in ["period", "year ended", "quarter ended"])
        ebitda_present = any(term in text_lower for term in ["EBITDA", "adjusted EBITDA"])
        revenue_recognition_present = "revenue recognition" in text_lower
        forecast_budget_present = any(term in text_lower for term in ["forecast", "projections", "budget"])
        qoe_present = any(term in text_lower for term in ["quality of earnings", "QoE"])
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'financials')
        
        return Financials(
            financial_statements_present=financial_statements_present,
            audited_unaudited_present=audited_unaudited_present,
            standard_present=standard_present,
            period_covered_present=period_covered_present,
            ebitda_present=ebitda_present,
            revenue_recognition_present=revenue_recognition_present,
            forecast_budget_present=forecast_budget_present,
            qoe_present=qoe_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_litigation(self, text: str) -> LitigationAndAllegations:
        """Analyze litigation and legal proceedings using comprehensive keyword matching."""
        
        # Use comprehensive bucket keyword matching
        litigation_present = self._check_bucket_keywords(text, 'litigation_claims', min_hits=2)
        
        text_lower = text.lower()
        
        # Enhanced detection using comprehensive keywords
        allegations_accusations_present = any(term in text_lower for term in ["allegation", "accusations", "complaint"])
        regulatory_investigation_present = any(term in text_lower for term in ["investigation", "inquiry", "subpoena"])
        demand_letters_present = any(term in text_lower for term in ["demand letter", "cease and desist"])
        settlement_consent_order_present = any(term in text_lower for term in ["settlement", "consent order", "injunction"])
        contingent_liability_reserves_present = any(term in text_lower for term in ["contingent liability", "provision", "reserve"])
        whistleblower_internal_investigation_present = any(term in text_lower for term in ["whistleblower", "internal investigation"])
        
        # Extract evidence snippets
        evidence_snippets = self._extract_bucket_evidence(text, 'litigation_claims')
        
        return LitigationAndAllegations(
            litigation_present=litigation_present,
            allegations_accusations_present=allegations_accusations_present,
            regulatory_investigation_present=regulatory_investigation_present,
            demand_letters_present=demand_letters_present,
            settlement_consent_order_present=settlement_consent_order_present,
            contingent_liability_reserves_present=contingent_liability_reserves_present,
            whistleblower_internal_investigation_present=whistleblower_internal_investigation_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_evidence_strength(self, text: str) -> EvidenceStrength:
        """Analyze the strength of evidence in the document."""
        
        numbers_present = bool(re.search(r'\d+', text))
        dates_present = any(re.search(pattern, text) for pattern in self.date_patterns)
        percentages_present = any(re.search(pattern, text) for pattern in self.percentage_patterns)
        defined_term_pattern_present = any(re.search(pattern, text, re.IGNORECASE) 
                                         for pattern in self.defined_term_patterns)
        schedule_exhibit_pattern_present = any(re.search(pattern, text, re.IGNORECASE) 
                                             for pattern in self.schedule_patterns)
        
        return EvidenceStrength(
            numbers_present=numbers_present,
            dates_present=dates_present,
            percentages_present=percentages_present,
            defined_term_pattern_present=defined_term_pattern_present,
            schedule_exhibit_pattern_present=schedule_exhibit_pattern_present
        )

    def _extract_first_date(self, text: str) -> str:
        """Extract the first date found in the text."""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return ""

    def _extract_date_near_term(self, text: str, terms: List[str]) -> str:
        """Extract a date near specific terms."""
        for term in terms:
            # Look for dates within 100 characters of the term
            pattern = f'{term}.{0,100}?' + '|'.join(self.date_patterns)
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract just the date part
                for date_pattern in self.date_patterns:
                    date_match = re.search(date_pattern, match.group(0))
                    if date_match:
                        return date_match.group(0)
        return ""

    def _check_bucket_keywords(self, text: str, bucket_name: str, min_hits: int = 1) -> bool:
        """Check if text contains minimum number of keywords from a bucket."""
        if bucket_name not in self.bucket_keywords:
            return False
        
        text_lower = text.lower()
        keywords = self.bucket_keywords[bucket_name]
        hits = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        return hits >= min_hits

    def _extract_bucket_evidence(self, text: str, bucket_name: str, max_snippets: int = 3) -> List[str]:
        """Extract evidence snippets for a bucket."""
        if bucket_name not in self.bucket_keywords:
            return []
        
        text_lower = text.lower()
        keywords = self.bucket_keywords[bucket_name]
        snippets = []
        
        for keyword in keywords:
            if len(snippets) >= max_snippets:
                break
            if keyword.lower() in text_lower:
                # Find the keyword in context
                start = text_lower.find(keyword.lower())
                if start != -1:
                    # Extract surrounding context (50 chars before and after)
                    context_start = max(0, start - 50)
                    context_end = min(len(text), start + len(keyword) + 50)
                    snippet = text[context_start:context_end].strip()
                    if snippet and snippet not in snippets:
                        snippets.append(snippet)
        
        return snippets

    def _analyze_covenants(self, text: str) -> Covenants:
        """Analyze covenants using comprehensive keyword matching."""
        
        section_present = self._check_bucket_keywords(text, 'covenants', min_hits=1)
        
        text_lower = text.lower()
        
        ordinary_course_present = "ordinary course" in text_lower
        negative_covenants_present = "negative covenant" in text_lower
        access_to_info_due_diligence_present = any(term in text_lower for term in ["access to information", "due diligence"])
        employee_matters_present = any(term in text_lower for term in ["employee matters", "retention"])
        confidentiality_noncompete_present = any(term in text_lower for term in ["non-compete", "non-solicit", "confidentiality"])
        tsa_transition_present = any(term in text_lower for term in ["transition services", "TSA"])
        
        evidence_snippets = self._extract_bucket_evidence(text, 'covenants')
        
        return Covenants(
            section_present=section_present,
            ordinary_course_present=ordinary_course_present,
            negative_covenants_present=negative_covenants_present,
            access_to_info_due_diligence_present=access_to_info_due_diligence_present,
            employee_matters_present=employee_matters_present,
            confidentiality_noncompete_present=confidentiality_noncompete_present,
            tsa_transition_present=tsa_transition_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_capital_debt(self, text: str) -> CapitalAndDebt:
        """Analyze capital structure and debt using comprehensive keyword matching."""
        
        text_lower = text.lower()
        
        cap_table_present = any(term in text_lower for term in ["cap table", "capitalization table"])
        securities_present = any(term in text_lower for term in ["options", "warrants", "convertibles", "SAFE", "preference shares"])
        debt_facility_present = any(term in text_lower for term in ["credit facility", "loan agreement", "debt"])
        liens_security_interest_present = any(term in text_lower for term in ["lien", "charge", "pledge", "security interest", "mortgage"])
        defaults_waivers_present = any(term in text_lower for term in ["default", "covenant breach", "waiver"])
        payoff_release_present = any(term in text_lower for term in ["payoff letter", "release of liens"])
        
        evidence_snippets = self._extract_bucket_evidence(text, 'capital_debt')
        
        return CapitalAndDebt(
            cap_table_present=cap_table_present,
            securities_present=securities_present,
            debt_facility_present=debt_facility_present,
            liens_security_interest_present=liens_security_interest_present,
            defaults_waivers_present=defaults_waivers_present,
            payoff_release_present=payoff_release_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_tax(self, text: str) -> Tax:
        """Analyze tax matters using comprehensive keyword matching."""
        
        text_lower = text.lower()
        
        tax_returns_present = "tax returns" in text_lower
        tax_audits_disputes_present = any(term in text_lower for term in ["tax audit", "assessment"])
        withholding_present = "withholding tax" in text_lower
        vat_gst_present = any(term in text_lower for term in ["VAT", "GST"])
        transfer_pricing_present = "transfer pricing" in text_lower
        tax_indemnity_covenant_present = any(term in text_lower for term in ["tax indemnity", "tax covenant"])
        
        evidence_snippets = self._extract_bucket_evidence(text, 'tax')
        
        return Tax(
            tax_returns_present=tax_returns_present,
            tax_audits_disputes_present=tax_audits_disputes_present,
            withholding_present=withholding_present,
            vat_gst_present=vat_gst_present,
            transfer_pricing_present=transfer_pricing_present,
            tax_indemnity_covenant_present=tax_indemnity_covenant_present,
            evidence_snippets=evidence_snippets
        )

    def _analyze_compliance(self, text: str) -> Compliance:
        """Analyze compliance matters using comprehensive keyword matching."""
        
        # Use comprehensive bucket keyword matching
        compliance_present = self._check_bucket_keywords(text, 'compliance', min_hits=1)
        
        text_lower = text.lower()
        
        anti_bribery_present = any(term in text_lower for term in ["anti-bribery", "anti-corruption", "FCPA", "UK bribery act"])
        aml_kyc_sanctions_present = any(term in text_lower for term in ["AML", "KYC", "sanctions", "OFAC"])
        competition_antitrust_present = any(term in text_lower for term in ["antitrust", "competition law"])
        privacy_data_protection_present = any(term in text_lower for term in ["PDPA", "GDPR", "data protection", "privacy"])
        cybersecurity_breach_present = any(term in text_lower for term in ["cybersecurity", "data breach"])
        export_controls_present = "export controls" in text_lower
        environment_hs_present = any(term in text_lower for term in ["health and safety", "environmental"])
        
        evidence_snippets = self._extract_bucket_evidence(text, 'compliance')
        
        return Compliance(
            anti_bribery_present=anti_bribery_present,
            aml_kyc_sanctions_present=aml_kyc_sanctions_present,
            competition_antitrust_present=competition_antitrust_present,
            privacy_data_protection_present=privacy_data_protection_present,
            cybersecurity_breach_present=cybersecurity_breach_present,
            export_controls_present=export_controls_present,
            environment_hs_present=environment_hs_present,
            evidence_snippets=evidence_snippets
        )
