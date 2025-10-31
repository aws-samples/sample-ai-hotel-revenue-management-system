#!/usr/bin/env python
"""
Quick test to verify that the system now uses the correct input data.
"""

import json
from src.hotel_revenue_optimization.main import run

def quick_test():
    """Quick test with the exact input from the user"""
    
    print("Testing with the exact input from the user...")
    
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
    print("\n" + "="*60 + "\n")
    
    # Run the agent
    print("Running the agent...")
    response = run(test_input)
    
    print(f"Status: {response.get('status', 'unknown')}")
    
    # Check if there's a report and if it contains the correct information
    if "report" in response and response["report"]:
        report = response["report"]
        print(f"Report generated: {len(report)} characters")
        
        # Key checks
        checks = [
            ("Your Business Hotel", "Hotel name"),
            ("New York", "Location"),
            ("$280", "ADR"),
            ("$196", "Current RevPAR"),
            ("$220", "Target RevPAR"),
        ]
        
        print("\nContent verification:")
        all_passed = True
        for search_term, description in checks:
            if search_term in report:
                print(f"✅ {description}: Found '{search_term}'")
            else:
                print(f"❌ {description}: '{search_term}' NOT FOUND")
                all_passed = False
        
        if all_passed:
            print("\n🎉 SUCCESS: All expected content found in the report!")
            print("The system is now using the correct input data.")
        else:
            print("\n❌ ISSUE: Some expected content was not found.")
            print("The system may still be using hardcoded values.")
        
        # Show a preview of the report
        print(f"\nReport preview (first 500 characters):")
        print("-" * 60)
        print(report[:500] + "..." if len(report) > 500 else report)
        print("-" * 60)
        
    else:
        print("❌ No report generated or report is empty")
        print("Full response:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    quick_test()
