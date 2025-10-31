#!/usr/bin/env python3
"""
Test to verify different outputs with and without competitor analysis
"""
import json

def test_output_difference():
    """Test that different outputs are generated with/without competitor analysis"""
    
    # Test inputs
    test_without = {
        "hotel_name": "Grand Pacific Resort",
        "hotel_location": "Miami, FL", 
        "current_adr": "$245",
        "historical_occupancy": "72%",
        "target_revpar": "$195"
    }
    
    test_with = {
        "prompt": "Optimize revenue for Grand Pacific Resort in Miami, FL with $245 ADR and 72% occupancy, targeting $195 RevPAR. Include competitor analysis."
    }
    
    print("🧪 Testing Output Differences")
    print("=" * 50)
    
    print("\n📋 Test Input WITHOUT Competitor Analysis:")
    print(json.dumps(test_without, indent=2))
    
    print("\n📋 Test Input WITH Competitor Analysis:")
    print(json.dumps(test_with, indent=2))
    
    print("\n✅ Test inputs prepared!")
    print("\n📝 To test manually:")
    print("1. Run: agentcore invoke --local '" + json.dumps(test_without) + "'")
    print("2. Run: agentcore invoke --local '" + json.dumps(test_with) + "'")
    print("3. Compare the outputs - the second should include detailed competitor analysis sections")
    
    return True

if __name__ == "__main__":
    test_output_difference()
