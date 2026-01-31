#!/usr/bin/env python3
"""
Test script for financial document completeness validation.
Tests the new financial-specific completeness rules.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent  # This file is in the project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.financial_completeness_analyzer import FinancialCompletenessAnalyzer
from src.extractors.tabular_text import extract_xlsx_text

def test_financial_completeness():
    """Test financial completeness with Abbott India file"""
    analyzer = FinancialCompletenessAnalyzer()
    
    # Test with Abbott India file
    abbott_file = PROJECT_ROOT / "Raw_Data_Files" / "Abbott India.xlsx"
    
    print(f"Looking for file at: {abbott_file}")
    print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"File exists: {abbott_file.exists()}")
    
    if abbott_file.exists():
        print(f"📊 Testing Financial Completeness Analysis with: {abbott_file.name}")
        print("=" * 80)
        
        # Extract text
        text = extract_xlsx_text(str(abbott_file))
        print(f"📄 Extracted {len(text)} characters from spreadsheet")
        
        # Analyze completeness
        result = analyzer.analyze_document(abbott_file.name, text)
        
        # Display results
        print(f"\n🎯 FINANCIAL COMPLETENESS RESULTS:")
        print(f"Document Type: {result.document_type}")
        print(f"Overall Score: {result.scores.overall_score}/100")
        print(f"Classification: {result.scores.classification}")
        
        print(f"\n📊 SCORE BREAKDOWN:")
        print(f"Financial Statements: {result.scores.financial_statements_score}/30")
        print(f"Performance Metrics: {result.scores.performance_metrics_score}/25") 
        print(f"Period Evidence: {result.scores.period_evidence_score}/25")
        print(f"Numeric Content: {result.scores.numeric_content_score}/20")
        
        print(f"\n📋 FINANCIAL STATEMENTS FOUND:")
        if result.financial_statements.profit_and_loss_present:
            print("✅ Profit & Loss Statement")
        if result.financial_statements.balance_sheet_present:
            print("✅ Balance Sheet") 
        if result.financial_statements.cash_flow_present:
            print("✅ Cash Flow Statement")
        if result.financial_statements.notes_present:
            print("✅ Notes to Financial Statements")
            
        if not any([
            result.financial_statements.profit_and_loss_present,
            result.financial_statements.balance_sheet_present,
            result.financial_statements.cash_flow_present
        ]):
            print("❌ No financial statements detected")
        
        print(f"\n🎯 PERFORMANCE METRICS FOUND:")
        metrics_found = 0
        if result.performance_metrics.sales_revenue_present:
            print("✅ Sales/Revenue")
            metrics_found += 1
        if result.performance_metrics.expenses_present:
            print("✅ Expenses")
            metrics_found += 1
        if result.performance_metrics.net_profit_present:
            print("✅ Net Profit")
            metrics_found += 1
        if result.performance_metrics.eps_present:
            print("✅ Earnings Per Share")
            metrics_found += 1
        if result.performance_metrics.ebitda_present:
            print("✅ EBITDA/Operating Profit")
            metrics_found += 1
        
        print(f"Total metrics found: {metrics_found}/5")
        
        print(f"\n📅 PERIOD EVIDENCE:")
        if result.period_evidence.fy_ending_present:
            print("✅ Financial Year Ending dates")
        if result.period_evidence.quarterly_dates_present:
            print("✅ Quarterly periods")
        if result.period_evidence.year_references_present:
            print("✅ Year references")
        if result.period_evidence.monthly_periods_present:
            print("✅ Monthly periods")
        
        print(f"\n🔢 NUMERIC EVIDENCE:")
        if result.numeric_evidence.currency_amounts_present:
            print("✅ Currency amounts")
        if result.numeric_evidence.substantial_numbers_present:
            print("✅ Substantial numbers")
        if result.numeric_evidence.percentages_present:
            print("✅ Percentages")
        if result.numeric_evidence.ratios_present:
            print("✅ Ratios")
        
        print(f"\n🚨 FLAGS:")
        if result.flags.no_financial_statements:
            print("❌ No financial statements found")
        if result.flags.insufficient_performance_metrics:
            print("⚠️  Insufficient performance metrics (need ≥2)")
        if result.flags.missing_period_evidence:
            print("❌ Missing period evidence")
        if result.flags.minimal_numeric_content:
            print("⚠️  Minimal numeric content")
        
        print(f"\n🎉 CONCLUSION:")
        if result.scores.classification == "accept_ok":
            print("✅ ACCEPT OK - Complete financial document")
        elif result.scores.classification == "accept_with_warnings":
            print("⚠️  ACCEPT WITH WARNINGS - Partial financial data")
        else:
            print("❌ REJECT INCOMPLETE - Insufficient financial data")
        
        # Show sample text for debugging
        print(f"\n🔍 SAMPLE TEXT (first 500 chars):")
        print(f"'{text[:500]}...'")
        
    else:
        print(f"❌ Abbott India file not found at: {abbott_file}")
        print("Available files in Raw_Data_Files:")
        raw_files_dir = PROJECT_ROOT / "Raw_Data_Files"
        if raw_files_dir.exists():
            for file in raw_files_dir.glob("*.xlsx"):
                print(f"  - {file.name}")

if __name__ == "__main__":
    test_financial_completeness()
