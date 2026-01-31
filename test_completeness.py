#!/usr/bin/env python3
"""
Test script for the enhanced deal completeness analyzer with 0-100 scoring
"""

from src.agents.deal_completeness_analyzer import DealCompletenessAnalyzer

def test_completeness_analyzer():
    """Test the completeness analyzer with various document types"""
    
    analyzer = DealCompletenessAnalyzer()
    
    # Test 1: Complete SPA document (should score 70-100, accept_ok)
    complete_spa = """
    SHARE PURCHASE AGREEMENT
    
    This Share Purchase Agreement (this "Agreement") is made on January 15, 2024, 
    between ABC Corp., a Delaware corporation ("Buyer"), and XYZ Holdings Ltd. ("Seller"),
    regarding the acquisition of Target Inc. ("Company").
    
    ARTICLE 1 - PURCHASE AND SALE
    Subject to the terms hereof, Seller agrees to sell the Target Shares
    for the Purchase Price of USD 50,000,000 (fifty million United States dollars).
    The Enterprise Value is $45,000,000 with 15% earnout based on EBITDA performance.
    
    ARTICLE 2 - REPRESENTATIONS AND WARRANTIES  
    Seller represents and warrants:
    (a) Organization and Authority: Full corporate power exists
    (b) Financial Statements: Audited statements per US GAAP present fairly
    (c) Material Contracts: All disclosed in Schedule 3.15  
    (d) Litigation: No pending matters per Disclosure Schedule 3.20
    (e) Material Adverse Effect: No MAE has occurred
    
    ARTICLE 3 - CONDITIONS TO CLOSING
    (a) Regulatory Approvals: All required approvals obtained
    (b) Third Party Consents: Material consents received
    (c) Bring-Down: Representations remain accurate
    
    ARTICLE 4 - INDEMNIFICATION
    (a) Indemnity: Seller indemnifies Buyer for breaches
    (b) Survival: 18 months from Closing
    (c) Basket: $100,000 threshold
    (d) Cap: Maximum $5,000,000 liability
    
    ARTICLE 5 - FINANCIAL INFORMATION
    Company's audited financial statements show EBITDA of $8,500,000.
    
    ARTICLE 6 - LITIGATION
    No litigation exists except as disclosed in Schedule 6.1.
    
    Governed by Delaware law. "Purchase Price" means amount in Article 1.
    """
    
    # Test 2: Marketing teaser (should score 0-49, reject_incomplete)
    teaser_doc = """
    STRATEGIC ACQUISITION OPPORTUNITY - CONFIDENTIAL TEASER
    
    XYZ Company Overview - Technology Sector Investment
    
    This presents an exciting strategic acquisition opportunity.
    Strong growth trajectory and significant synergies expected.
    
    Key highlights:
    - Market-leading position in growing sector
    - Experienced management team with proven track record  
    - Significant cross-selling and cost synergy opportunities
    - Strong financial performance with consistent growth
    - Well-positioned for continued expansion
    
    Next Steps:
    Interested parties should contact advisors for additional information.
    """
    
    # Test 3: Term sheet (should score 50-69, accept_with_warnings)  
    term_sheet = """
    TERM SHEET - ACQUISITION OF TARGET COMPANY
    
    Buyer: ABC Corp
    Seller: XYZ Holdings  
    Target: Target Inc.
    
    Purchase Price: $50,000,000 cash at closing
    Structure: Asset purchase agreement
    Signing: On or before March 1, 2024
    Closing: 60 days after signing
    
    Key Terms:
    - Representations and warranties: Standard for transaction of this type
    - Material adverse change: Standard definition
    - Regulatory approvals: Antitrust clearance required
    - Due diligence: 45-day period
    - Break fee: 3% of purchase price
    
    This term sheet is non-binding except for exclusivity and confidentiality.
    """
    
    print("=== Enhanced Completeness Analyzer Test (0-100 Scoring) ===\n")
    
    print("1. Complete SPA Document:")
    result1 = analyzer.analyze_document("spa_complete.pdf", complete_spa)
    print(f"   - Bucket Score: {result1.scores.bucket_coverage_score}/70")
    print(f"   - Evidence Score: {result1.scores.evidence_strength_score}/30") 
    print(f"   - Overall Score: {result1.scores.overall_score}/100")
    print(f"   - Classification: {result1.scores.classification}")
    if result1.flags.missing_core_buckets:
        print(f"   - Missing Buckets: {result1.flags.missing_core_buckets}")
    print()
    
    print("2. Marketing Teaser:")
    result2 = analyzer.analyze_document("teaser.pdf", teaser_doc)
    print(f"   - Bucket Score: {result2.scores.bucket_coverage_score}/70")
    print(f"   - Evidence Score: {result2.scores.evidence_strength_score}/30")
    print(f"   - Overall Score: {result2.scores.overall_score}/100") 
    print(f"   - Classification: {result2.scores.classification}")
    print(f"   - Likely Teaser: {result2.flags.likely_teaser_or_summary}")
    print(f"   - Missing Buckets: {result2.flags.missing_core_buckets}")
    print()
    
    print("3. Term Sheet:")
    result3 = analyzer.analyze_document("term_sheet.pdf", term_sheet)
    print(f"   - Bucket Score: {result3.scores.bucket_coverage_score}/70")
    print(f"   - Evidence Score: {result3.scores.evidence_strength_score}/30")
    print(f"   - Overall Score: {result3.scores.overall_score}/100")
    print(f"   - Classification: {result3.scores.classification}")
    print(f"   - Likely Teaser/LOI: {result3.flags.likely_teaser_or_summary}")
    if result3.flags.missing_core_buckets:
        print(f"   - Missing Buckets: {result3.flags.missing_core_buckets}")
    
    return result1, result2, result3

if __name__ == "__main__":
    test_completeness_analyzer()
