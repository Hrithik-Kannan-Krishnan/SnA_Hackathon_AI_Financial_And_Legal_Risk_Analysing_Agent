#!/usr/bin/env python3

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extractors.tabular_text import extract_xlsx_text
from src.agents.financial_completeness_analyzer import FinancialCompletenessAnalyzer
import pandas as pd

def analyze_file_detailed(file_path):
    """Analyze a single file in detail"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {file_path}")
    print(f"{'='*80}")
    
    try:
        # Extract text
        text = extract_xlsx_text(file_path)
        print(f"Extracted text length: {len(text)} characters")
        print(f"First 300 chars: {repr(text[:300])}")
        print(f"Last 300 chars: {repr(text[-300:])}")
        
        # Analyze with financial completeness
        analyzer = FinancialCompletenessAnalyzer()
        result = analyzer.analyze_document(text, file_path)
        
        print(f"\nFINANCIAL COMPLETENESS RESULT:")
        print(f"Overall Score: {result.scores.overall_score}/100")
        print(f"Classification: {result.scores.classification}")
        
        print(f"\nDetailed Scores:")
        print(f"- Financial Statements: {result.scores.financial_statements_score}/30")
        print(f"- Performance Metrics: {result.scores.performance_metrics_score}/25") 
        print(f"- Period Evidence: {result.scores.period_evidence_score}/25")
        print(f"- Numeric Content: {result.scores.numeric_content_score}/20")
        
        print(f"\nFlags:")
        flags_dict = result.flags.model_dump()
        for key, value in flags_dict.items():
            if value:
                print(f"- {key}: {value}")
        
        # Let's also check the individual analysis components
        print(f"\nDETAILED ANALYSIS:")
        
        # Check financial statements
        statements = result.financial_statements
        print(f"Financial Statements Found: {len(statements.statement_types)}")
        for stmt_type in statements.statement_types:
            print(f"  - {stmt_type}")
        print(f"Statement Keywords: {statements.statement_keywords[:10]}...")
        
        # Check performance metrics
        metrics = result.performance_metrics
        print(f"Performance Metrics Found: {len(metrics.metric_types)}")
        for metric_type in metrics.metric_types:
            print(f"  - {metric_type}")
        print(f"Performance Keywords: {metrics.performance_keywords[:10]}...")
        
        # Check period evidence
        period = result.period_evidence
        print(f"Period Types Found: {len(period.period_types)}")
        for period_type in period.period_types:
            print(f"  - {period_type}")
        print(f"Period Keywords: {period.period_keywords[:10]}...")
        
        # Check numeric evidence
        numeric = result.numeric_evidence
        print(f"Numeric Types Found: {len(numeric.numeric_types)}")
        for num_type in numeric.numeric_types:
            print(f"  - {num_type}")
        print(f"Amounts Found: {len(numeric.amounts)}")
        print(f"Percentages Found: {len(numeric.percentages)}")
        
        return result
        
    except Exception as e:
        print(f"ERROR analyzing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    # Test files
    test_files = [
        "/Users/hrithikkannankrishnan/Desktop/hackathons/SnA/Raw_Data_Files/Abbott India.xlsx",
        "/Users/hrithikkannankrishnan/Desktop/hackathons/SnA/Raw_Data_Files/Avenue Super.xlsx", 
        "/Users/hrithikkannankrishnan/Desktop/hackathons/SnA/Raw_Data_Files/Divi's Lab.xlsx",
        "/Users/hrithikkannankrishnan/Desktop/hackathons/SnA/Raw_Data_Files/Page Industries.xlsx",
        "/Users/hrithikkannankrishnan/Desktop/hackathons/SnA/Raw_Data_Files/Relaxo Footwear.xlsx"
    ]
    
    results = []
    for file_path in test_files:
        if Path(file_path).exists():
            result = analyze_file_detailed(file_path)
            if result:
                results.append({
                    'file': Path(file_path).name,
                    'score': result.scores.overall_score,
                    'classification': result.scores.classification,
                    'text_length': len(extract_xlsx_text(file_path))
                })
        else:
            print(f"File not found: {file_path}")
    
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    
    for r in results:
        print(f"{r['file']:20} | Score: {r['score']:3}/100 | Class: {r['classification']:15} | Text: {r['text_length']:5} chars")

if __name__ == "__main__":
    main()
