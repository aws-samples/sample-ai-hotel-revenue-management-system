#!/usr/bin/env python3
"""
Test script to verify competitor analysis instruction detection
"""
import sys
import os
sys.path.append('src')

from hotel_revenue_optimization.utils.nlp_processor import NLPProcessor

def test_competitor_analysis_detection():
    """Test that competitor analysis instructions are properly detected"""
    
    nlp = NLPProcessor()
    
    # Test cases
    test_cases = [
        {
            "input": "Optimize revenue for Grand Hotel in Miami with $200 ADR and 70% occupancy. Include competitor analysis.",
            "should_include": True,
            "description": "Basic competitor analysis request"
        },
        {
            "input": "Analyze pricing for Seaside Resort in San Francisco with competitor analysis included",
            "should_include": True,
            "description": "Competitor analysis included variant"
        },
        {
            "input": "Revenue optimization for Downtown Hotel in Chicago with $180 ADR, add competitor analysis",
            "should_include": True,
            "description": "Add competitor analysis variant"
        },
        {
            "input": "Optimize revenue for Beach Resort in Miami with $250 ADR and 65% occupancy",
            "should_include": False,
            "description": "No competitor analysis requested"
        },
        {
            "input": "Help with pricing strategy for luxury hotel in New York with competitor pricing analysis",
            "should_include": True,
            "description": "With competitor analysis variant"
        }
    ]
    
    print("🧪 Testing Competitor Analysis Detection")
    print("=" * 50)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"Input: {test_case['input']}")
        
        result = nlp.process_input(test_case['input'])
        
        has_competitor_analysis = result.get('include_competitor_analysis') == 'true'
        expected = test_case['should_include']
        
        if has_competitor_analysis == expected:
            print(f"✅ PASS - Competitor analysis detected: {has_competitor_analysis}")
        else:
            print(f"❌ FAIL - Expected: {expected}, Got: {has_competitor_analysis}")
            all_passed = False
        
        # Show relevant extracted data
        print(f"   Hotel: {result.get('hotel_name', 'Not detected')}")
        print(f"   Location: {result.get('hotel_location', 'Not detected')}")
        print(f"   ADR: {result.get('current_adr', 'Not detected')}")
        print(f"   Competitor Analysis: {result.get('include_competitor_analysis', 'false')}")
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests PASSED!")
        return True
    else:
        print("❌ Some tests FAILED!")
        return False

if __name__ == "__main__":
    success = test_competitor_analysis_detection()
    sys.exit(0 if success else 1)
