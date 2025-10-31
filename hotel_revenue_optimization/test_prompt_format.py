#!/usr/bin/env python
"""
Test script to verify that the system handles the {"prompt": "..."} format correctly.
"""

import json
from src.hotel_revenue_optimization.main import run

def test_prompt_format():
    """Test with the exact format that the UI is sending"""
    
    print("Testing with UI prompt format...")
    
    # This is the exact format your UI is sending
    test_input = {
        "prompt": "Optimize revenue for Seaside Resort in San Francisco with 85% occupancy and $350 ADR"
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
        
        # Key checks for Seaside Resort and San Francisco
        checks = [
            ("Seaside Resort", "Hotel name"),
            ("San Francisco", "Location"),
            ("$350", "ADR"),
            ("85%", "Occupancy"),
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
            print("The system is now correctly processing the UI prompt format.")
        else:
            print("\n❌ ISSUE: Some expected content was not found.")
            print("The system may still not be processing the prompt correctly.")
        
        # Show a preview of the report
        print(f"\nReport preview (first 500 characters):")
        print("-" * 60)
        print(report[:500] + "..." if len(report) > 500 else report)
        print("-" * 60)
        
    else:
        print("❌ No report generated or report is empty")
        print("Full response:")
        print(json.dumps(response, indent=2))

def test_message_format():
    """Test with the AgentCore CLI message format"""
    
    print("\n" + "="*80 + "\n")
    print("Testing with AgentCore CLI message format...")
    
    test_input = {
        "message": "Optimize revenue for Mountain View Resort in Denver with 70% occupancy and $180 ADR"
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
        
        # Key checks for Mountain View Resort and Denver
        checks = [
            ("Mountain View Resort", "Hotel name"),
            ("Denver", "Location"),
            ("$180", "ADR"),
            ("70%", "Occupancy"),
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
            print("\n🎉 SUCCESS: AgentCore CLI format also working!")
        else:
            print("\n❌ ISSUE: Some expected content was not found.")

if __name__ == "__main__":
    test_prompt_format()
    test_message_format()
