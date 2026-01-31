"""
Financial document completeness analyzer.
Analyzes financial spreadsheets and reports for completeness using financial-specific criteria.
"""
import re
from typing import Dict, List, Tuple
from pathlib import Path

from src.agents.financial_completeness_schema import (
    FinancialCompletenessAnalysis,
    FinancialDocumentType,
    FinancialStatementType,
    PerformanceMetrics,
    PeriodEvidence,
    NumericEvidence,
    FinancialCompletenessScores,
    FinancialCompletenessFlags,
)

class FinancialCompletenessAnalyzer:
    """Analyzer for financial document completeness validation"""
    
    def __init__(self):
        # Financial statement sheet name patterns
        self.statement_patterns = {
            "profit_and_loss": [
                r"profit.*loss", r"p\s*&\s*l", r"income.*statement", r"pnl", 
                r"statement.*income", r"profit.*account", r"trading.*account",
                r"revenue.*account", r"pl\s+statement", r"income.*expenses"
            ],
            "balance_sheet": [
                r"balance.*sheet", r"b\s*/\s*s", r"bs", r"financial.*position",
                r"statement.*financial.*position", r"assets.*liabilities",
                r"balance.*statement"
            ],
            "cash_flow": [
                r"cash.*flow", r"cashflow", r"c\s*/\s*f", r"cf", r"cash.*statement",
                r"statement.*cash.*flow", r"fund.*flow"
            ]
        }
        
        # Performance metrics keywords
        self.performance_keywords = {
            "sales_revenue": [
                r"sales", r"revenue", r"turnover", r"income from operations",
                r"gross revenue", r"net sales", r"operating revenue", r"total income",
                r"sale of goods", r"service revenue"
            ],
            "expenses": [
                r"expenses", r"cost of goods sold", r"cogs", r"operating expenses",
                r"administrative expenses", r"selling expenses", r"total expenses",
                r"cost of sales", r"opex", r"overheads", r"expenditure"
            ],
            "net_profit": [
                r"net profit", r"net income", r"pat", r"profit after tax",
                r"net earnings", r"bottom line", r"profit for the year",
                r"comprehensive income"
            ],
            "eps": [
                r"earnings per share", r"eps", r"basic eps", r"diluted eps",
                r"earning per equity share"
            ],
            "ebitda": [
                r"ebitda", r"ebit", r"operating profit", r"operating income",
                r"profit before interest", r"earnings before"
            ]
        }
        
        # Period/date patterns
        self.period_patterns = [
            r"fy\s*\d{4}", r"financial year", r"fy ending", r"year ended",
            r"march\s*\d{4}", r"31st march", r"31-mar", r"march 31",
            r"q[1-4]\s*fy\s*\d{2,4}", r"quarter", r"quarterly", r"half.*year",
            r"2019|2020|2021|2022|2023|2024", r"h1\s*fy", r"h2\s*fy"
        ]
        
        # Numeric content patterns
        self.numeric_patterns = [
            r"₹[\d,]+", r"rs\.?\s*[\d,]+", r"inr[\d,]+",  # Currency
            r"\$[\d,]+", r"usd[\d,]+",  # USD
            r"[\d,]+\.?\d*\s*crore", r"[\d,]+\.?\d*\s*lakh",  # Indian units
            r"\d+\.\d+%", r"\d+%",  # Percentages
            r"\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b"  # Large numbers with commas
        ]

    def analyze_document(self, filename: str, text: str) -> FinancialCompletenessAnalysis:
        """Main entry point for financial document analysis"""
        
        # Determine document type
        doc_type = self._determine_document_type(filename, text)
        
        # Analyze different aspects
        statements = self._analyze_financial_statements(text)
        performance = self._analyze_performance_metrics(text)
        periods = self._analyze_period_evidence(text)
        numeric = self._analyze_numeric_evidence(text)
        
        # Calculate scores before creating the analysis object
        scores, flags = self._calculate_scores(statements, performance, periods, numeric)
        
        # Create analysis object with calculated scores
        analysis = FinancialCompletenessAnalysis(
            document_type=doc_type,
            financial_statements=statements,
            performance_metrics=performance,
            period_evidence=periods,
            numeric_evidence=numeric,
            scores=scores,
            flags=flags
        )
        
        return analysis
    
    def _determine_document_type(self, filename: str, text: str) -> FinancialDocumentType:
        """Determine if document is spreadsheet or report"""
        ext = Path(filename).suffix.lower()
        if ext in ['.xlsx', '.xls', '.csv']:
            return FinancialDocumentType.FINANCIAL_SPREADSHEET
        return FinancialDocumentType.FINANCIAL_REPORT
    
    def _analyze_financial_statements(self, text: str) -> FinancialStatementType:
        """Check for presence of core financial statements"""
        text_lower = text.lower()
        
        statements = FinancialStatementType()
        
        # Check for P&L
        for pattern in self.statement_patterns["profit_and_loss"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                statements.profit_and_loss_present = True
                break
        
        # Check for Balance Sheet
        for pattern in self.statement_patterns["balance_sheet"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                statements.balance_sheet_present = True
                break
        
        # Check for Cash Flow
        for pattern in self.statement_patterns["cash_flow"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                statements.cash_flow_present = True
                break
        
        # Check for notes
        if re.search(r"notes?.*to.*financial|notes?.*to.*accounts|significant.*accounting", text_lower):
            statements.notes_present = True
        
        return statements
    
    def _analyze_performance_metrics(self, text: str) -> PerformanceMetrics:
        """Check for presence of key performance metrics"""
        text_lower = text.lower()
        
        metrics = PerformanceMetrics()
        
        # Sales/Revenue
        for pattern in self.performance_keywords["sales_revenue"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                metrics.sales_revenue_present = True
                break
        
        # Expenses
        for pattern in self.performance_keywords["expenses"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                metrics.expenses_present = True
                break
        
        # Net Profit
        for pattern in self.performance_keywords["net_profit"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                metrics.net_profit_present = True
                break
        
        # EPS
        for pattern in self.performance_keywords["eps"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                metrics.eps_present = True
                break
        
        # EBITDA
        for pattern in self.performance_keywords["ebitda"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                metrics.ebitda_present = True
                break
        
        return metrics
    
    def _analyze_period_evidence(self, text: str) -> PeriodEvidence:
        """Check for presence of period/date evidence with improved detection"""
        text_lower = text.lower()
        
        periods = PeriodEvidence()
        
        # More specific and discriminating period patterns
        fy_patterns = [r"fy\s*(?:20\d{2}|1\d{3})", r"financial year.*(?:20\d{2}|1\d{3})", r"year.*end.*(?:20\d{2}|1\d{3})"]
        quarterly_patterns = [r"q[1-4].*(?:20\d{2}|fy)", r"quarter.*(?:end|20\d{2})", r"half.*year.*(?:20\d{2})"]
        year_patterns = [r"\b20[1-2]\d\b", r"\b1[89]\d{2}\b"]  # More specific year patterns
        month_patterns = [r"march.*20\d{2}", r"mar.*20\d{2}", r"31.*march", r"31-mar"]
        
        # Check for FY ending with actual years
        for pattern in fy_patterns:
            if re.search(pattern, text_lower):
                periods.fy_ending_present = True
                break
        
        # Check for quarterly patterns
        for pattern in quarterly_patterns:
            if re.search(pattern, text_lower):
                periods.quarterly_dates_present = True
                break
        
        # Look for actual year references in data context
        year_matches = []
        for pattern in year_patterns:
            matches = re.findall(pattern, text)
            year_matches.extend(matches)
        
        # Only set if we have multiple years (indicating time series)
        unique_years = set(year_matches)
        periods.year_references_present = len(unique_years) >= 2
        
        # Check for month patterns with years
        for pattern in month_patterns:
            if re.search(pattern, text_lower):
                periods.monthly_periods_present = True
                break
        
        return periods
    
    def _analyze_numeric_evidence(self, text: str) -> NumericEvidence:
        """Analyze numeric content richness with improved discrimination"""
        evidence = NumericEvidence()
        
        # More sophisticated numeric analysis
        currency_matches = []
        for pattern in self.numeric_patterns[:3]:  # Currency patterns
            matches = re.findall(pattern, text, re.IGNORECASE)
            currency_matches.extend(matches)
        
        percentage_matches = re.findall(r"\d+\.?\d*%", text)
        large_number_matches = re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b", text)
        
        # Count actual numeric values (not just zeros or empty cells)
        meaningful_numbers = re.findall(r"\b(?!0+\.?0*\b)\d{1,}(?:[,\.]\d+)*\b", text)
        non_zero_numbers = [n for n in meaningful_numbers if not re.match(r"^0+\.?0*$", n)]
        
        # Count rows with actual data (not just headers or empty rows)
        lines = text.split('\n')
        data_rows = [line for line in lines if re.search(r'\d{3,}', line)]  # Lines with substantial numbers
        
        # More discriminating thresholds based on actual content
        evidence.currency_amounts_present = len(currency_matches) >= 3 and len([m for m in currency_matches if not re.match(r'.*0+\.?0*.*', m)]) >= 1
        evidence.percentages_present = len(percentage_matches) >= 2
        evidence.substantial_numbers_present = len(non_zero_numbers) >= 15 and len(data_rows) >= 5
        
        # Enhanced ratio detection
        ratio_patterns = [r"\b\d+\.\d{2,}\b", r"\b\d+:\d+\b"]  # More specific ratios
        ratio_count = sum(len(re.findall(pattern, text, re.IGNORECASE)) for pattern in ratio_patterns)
        evidence.ratios_present = ratio_count >= 3 and len(non_zero_numbers) >= 10
        
        return evidence
    
    def _calculate_scores(self, statements: FinancialStatementType, performance: PerformanceMetrics, 
                         periods: PeriodEvidence, numeric: NumericEvidence) -> Tuple[FinancialCompletenessScores, FinancialCompletenessFlags]:
        """Calculate scores and flags based on analysis results"""
        
        # Financial Statements Score (0-30 points)
        statements_score = 0
        if statements.profit_and_loss_present:
            statements_score += 12
        if statements.balance_sheet_present:
            statements_score += 10
        if statements.cash_flow_present:
            statements_score += 8
        
        # Performance Metrics Score (0-25 points) - need at least 2 metrics
        performance_count = performance.performance_items_count
        if performance_count >= 3:
            performance_score = 25
        elif performance_count == 2:
            performance_score = 20
        elif performance_count == 1:
            performance_score = 10
        else:
            performance_score = 0
        
        # Period Evidence Score (0-25 points) with more discriminating scoring
        period_score = 0
        if periods.fy_ending_present:
            period_score += 12  # Higher weight for specific FY dates
        if periods.year_references_present:
            period_score += 8   # Multiple years indicate time series
        if periods.quarterly_dates_present:
            period_score += 4
        if periods.monthly_periods_present:
            period_score += 3
        period_score = min(period_score, 25)
        
        # Numeric Content Score (0-20 points) - enhanced scoring
        numeric_score = numeric.numeric_content_score
        
        # Apply data quality penalty for template-like content
        data_quality_penalty = 0
        if not numeric.substantial_numbers_present and not numeric.currency_amounts_present:
            data_quality_penalty = 10  # Heavy penalty for no meaningful numbers
        elif not numeric.substantial_numbers_present:
            data_quality_penalty = 5   # Moderate penalty for limited numbers
        
        # Calculate total score with penalty
        total_score = statements_score + performance_score + period_score + numeric_score - data_quality_penalty
        total_score = max(0, total_score)  # Don't go below 0
        
        # Create flags with enhanced detection
        flags = FinancialCompletenessFlags(
            no_financial_statements=not any([
                statements.profit_and_loss_present,
                statements.balance_sheet_present,
                statements.cash_flow_present,
            ]),
            insufficient_performance_metrics=performance_count < 2,
            missing_period_evidence=not periods.has_period_evidence,
            minimal_numeric_content=not numeric.substantial_numbers_present and not numeric.currency_amounts_present,
            likely_cover_page_only=statements_score == 0 and performance_score == 0,
            likely_notes_only=statements_score > 0 and numeric_score < 5
        )
        
        # Enhanced classification logic
        if total_score >= 80:
            classification = "accept_ok"
        elif total_score >= 55:
            classification = "accept_with_warnings"
        else:
            classification = "reject_incomplete"
        
        # Hard fail rules for financial documents
        if flags.no_financial_statements and flags.insufficient_performance_metrics:
            classification = "reject_incomplete"
            total_score = min(total_score, 25)  # Cap at 25 for hard fails
        
        # Additional penalty for template-like content
        if flags.minimal_numeric_content and period_score < 10:
            classification = "accept_with_warnings"  # Demote if no real data
            if total_score < 40:
                classification = "reject_incomplete"
        
        # Create scores object
        scores = FinancialCompletenessScores(
            financial_statements_score=statements_score,
            performance_metrics_score=performance_score,
            period_evidence_score=period_score,
            numeric_content_score=numeric_score,
            overall_score=total_score,
            classification=classification
        )
        
        return scores, flags
