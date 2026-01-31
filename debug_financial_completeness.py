#!/usr/bin/env python3
"""
Debug script to compare financial completeness analysis between different files.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.financial_completeness_analyzer import FinancialCompletenessAnalyzer
from src.extractors.tabular_text import extract_xlsx_text

def compare_financial_files():
    """Compare financial completeness analysis for different files"""
    analyzer = FinancialCompletenessAnalyzer()
    
    # Test files
    test_files = [
        "Abbott India.xlsx",
        "Avenue Super.xlsx", 
        "Divi's Lab.xlsx",
        "Page Industries.xlsx",
        "Relaxo Footwear.xlsx"
    ]
    
    print("🔍 FINANCIAL COMPLETENESS COMPARISON")
    print("=" * 80)
    
    for filename in test_files:
        file_path = PROJECT_ROOT / "Raw_Data_Files" / filename
        
        if not file_path.exists():
            print(f"❌ {filename} - File not found")
            continue
            
        print(f"\n📊 ANALYZING: {filename}")
        print("-" * 60)
        
        try:
            # Extract text
            text = extract_xlsx_text(str(file_path))
            print(f"📄 Extracted {len(text)} characters")
            
            # Analyze each component separately for debugging
            statements = analyzer._analyze_financial_statements(text)
            performance = analyzer._analyze_performance_metrics(text)
            periods = analyzer._analyze_period_evidence(text)
            numeric = analyzer._analyze_numeric_evidence(text)
            
            print(f"\n📋 STATEMENTS:")
            print(f"  P&L: {statements.profit_and_loss_present}")
            print(f"  Balance Sheet: {statements.balance_sheet_present}")
            print(f"  Cash Flow: {statements.cash_flow_present}")
            
            print(f"\n🎯 PERFORMANCE:")
            print(f"  Sales: {performance.sales_revenue_present}")
            print(f"  Expenses: {performance.expenses_present}")
            print(f"  Net Profit: {performance.net_profit_present}")
            print(f"  EPS: {performance.eps_present}")
            print(f"  EBITDA: {performance.ebitda_present}")
            print(f"  Total metrics: {performance.performance_items_count}")
            
            print(f"\n📅 PERIODS:")
            print(f"  FY ending: {periods.fy_ending_present}")
            print(f"  Quarterly: {periods.quarterly_dates_present}")
            print(f"  Year refs: {periods.year_references_present}")
            print(f"  Monthly: {periods.monthly_periods_present}")
            
            print(f"\n🔢 NUMERIC EVIDENCE:")
            # Show actual counts for debugging
            import re
            currency_count = 0
            for pattern in analyzer.numeric_patterns[:3]:
                matches = re.findall(pattern, text, re.IGNORECASE)
                currency_count += len(matches)
            
            percentage_matches = re.findall(r"\d+\.?\d*%", text)
            large_number_matches = re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d{2})?\b", text)
            
            print(f"  Currency matches: {currency_count} (threshold: 5)")
            print(f"  Percentage matches: {len(percentage_matches)} (threshold: 3)")
            print(f"  Large numbers: {len(large_number_matches)} (threshold: 10)")
            print(f"  Currency present: {numeric.currency_amounts_present}")
            print(f"  Percentages present: {numeric.percentages_present}")
            print(f"  Substantial numbers: {numeric.substantial_numbers_present}")
            print(f"  Ratios present: {numeric.ratios_present}")
            
            # Full analysis
            result = analyzer.analyze_document(filename, text)
            print(f"\n🎉 FINAL SCORES:")
            print(f"  Overall: {result.scores.overall_score}/100")
            print(f"  Statements: {result.scores.financial_statements_score}/30")
            print(f"  Performance: {result.scores.performance_metrics_score}/25")
            print(f"  Period: {result.scores.period_evidence_score}/25")
            print(f"  Numeric: {result.scores.numeric_content_score}/20")
            print(f"  Classification: {result.scores.classification}")
            
            # Show first 500 chars for comparison
            print(f"\n🔍 SAMPLE TEXT:")
            print(f"'{text[:500]}...'")
            
        except Exception as e:
            print(f"❌ Error analyzing {filename}: {e}")

if __name__ == "__main__":
    compare_financial_files()
