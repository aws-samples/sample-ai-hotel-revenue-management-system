#!/usr/bin/env python
"""
Test script to verify that inputs are being processed correctly.
"""

import json
from src.hotel_revenue_optimization.main import run

def test_structured_input():
    """Test with structured JSON input"""
    print("Testing structured JSON input...")
    
    test_input = {
        "hotel_name": "Your Business Hotel",
        "hotel_location": "New York, NY",
        "hotel_rating": "4.0",
        "room_types": "Standard, Business, Suite",
        "analysis_period": "Next 90 days",
        "forecast_period": "Next 90 days",
        "historical_occupancy": "70%",
        "current_adr": "$280",
        "current_revpar": "$196",
        "target_revpar": "$220",
        "current_challenges": "Weekday occupancy fluctuations, corporate booking patterns"
    }
    
    print("Input:")
    print(json.dumps(test_input, indent=2))
    print("\n" + "="*80 + "\n")
    
    # Run the agent
    response = run(test_input)
    
    print("Response status:", response.get("status", "unknown"))
    
    # Check if there's a report
    if "report" in response:
        report = response["report"]
        print("\nReport preview (first 1000 characters):")
        print(report[:1000] + "..." if len(report) > 1000 else report)
        
        # Check if the report contains the correct hotel information
        if "Your Business Hotel" in report:
            print("\n✅ SUCCESS: Report contains the correct hotel name!")
        else:
            print("\n❌ ERROR: Report does not contain the correct hotel name!")
            
        if "New York, NY" in report:
            print("✅ SUCCESS: Report contains the correct location!")
        else:
            print("❌ ERROR: Report does not contain the correct location!")
            
        if "$280" in report:
            print("✅ SUCCESS: Report contains the correct ADR!")
        else:
            print("❌ ERROR: Report does not contain the correct ADR!")
    else:
        print("\n❌ ERROR: No report generated!")
        print("Full response:")
        print(json.dumps(response, indent=2))

def test_natural_language_input():
    """Test with natural language input"""
    print("\n" + "="*80 + "\n")
    print("Testing natural language input...")
    
    test_input = "Optimize revenue for Seaside Resort in San Francisco, CA with luxury suites and standard rooms. Current occupancy is 85%, ADR $350, RevPAR $297.50, target RevPAR $320 for the next quarter."
    
    print("Input:")
    print(test_input)
    print("\n" + "="*80 + "\n")
    
    # Run the agent
    response = run(test_input)
    
    print("Response status:", response.get("status", "unknown"))
    
    # Check if there's a report
    if "report" in response:
        report = response["report"]
        print("\nReport preview (first 1000 characters):")
        print(report[:1000] + "..." if len(report) > 1000 else report)
        
        # Check if the report contains the correct hotel information
        if "Seaside Resort" in report:
            print("\n✅ SUCCESS: Report contains the correct hotel name!")
        else:
            print("\n❌ ERROR: Report does not contain the correct hotel name!")
            
        if "San Francisco" in report:
            print("✅ SUCCESS: Report contains the correct location!")
        else:
            print("❌ ERROR: Report does not contain the correct location!")
            
        if "$350" in report:
            print("✅ SUCCESS: Report contains the correct ADR!")
        else:
            print("❌ ERROR: Report does not contain the correct ADR!")
    else:
        print("\n❌ ERROR: No report generated!")
        print("Full response:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    test_structured_input()
    test_natural_language_input()
