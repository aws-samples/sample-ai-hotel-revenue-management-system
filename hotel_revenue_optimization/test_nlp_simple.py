#!/usr/bin/env python3
"""
Simple test for NLP processor competitor analysis detection
"""
import sys
import os
import re
import json
from typing import Dict, Any, Union, Optional

# Simplified NLP processor test
class TestNLPProcessor:
    def __init__(self):
        # Optional instruction patterns
        self.optional_instructions = {
            r'include\s+competitor\s+analysis': 'include_competitor_analysis',
            r'with\s+competitor\s+analysis': 'include_competitor_analysis',
            r'add\s+competitor\s+analysis': 'include_competitor_analysis',
            r'competitor\s+analysis\s+included': 'include_competitor_analysis'
        }
    
    def _detect_optional_instructions(self, text: str) -> Dict[str, bool]:
        """Detect optional instructions in the input text."""
        instructions = {}
        
        for pattern, instruction_key in self.optional_instructions.items():
            if re.search(pattern, text, re.IGNORECASE):
                instructions[instruction_key] = True
        
        return instructions
    
    def test_detection(self, text: str) -> Dict[str, Any]:
        """Test detection of competitor analysis instruction"""
        optional_instructions = self._detect_optional_instructions(text)
        
        result = {
            'text': text,
            'detected_instructions': optional_instructions,
            'include_competitor_analysis': optional_instructions.get('include_competitor_analysis', False)
        }
        
        return result

def test_competitor_analysis_detection():
    """Test that competitor analysis instructions are properly detected"""
    
    nlp = TestNLPProcessor()
    
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
            "input": "Help with pricing strategy for luxury hotel in New York with competitor analysis",
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
        
        result = nlp.test_detection(test_case['input'])
        
        has_competitor_analysis = result['include_competitor_analysis']
        expected = test_case['should_include']
        
        if has_competitor_analysis == expected:
            print(f"✅ PASS - Competitor analysis detected: {has_competitor_analysis}")
        else:
            print(f"❌ FAIL - Expected: {expected}, Got: {has_competitor_analysis}")
            all_passed = False
        
        # Show detected instructions
        if result['detected_instructions']:
            print(f"   Detected instructions: {result['detected_instructions']}")
        else:
            print(f"   No optional instructions detected")
    
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
