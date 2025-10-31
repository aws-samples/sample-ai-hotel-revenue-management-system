#!/usr/bin/env python
"""
Debug script to test input processing in isolation.
"""

import json
from src.hotel_revenue_optimization.utils.nlp_processor import NLPProcessor

def test_nlp_processor():
    """Test the NLP processor with different inputs"""
    
    nlp = NLPProcessor()
    
    # Test 1: Dictionary input
    print("=== Test 1: Dictionary Input ===")
    dict_input = {
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
    print(json.dumps(dict_input, indent=2))
    
    result = nlp.process_input(dict_input)
    print("\nProcessed result:")
    print(json.dumps(result, indent=2))
    
    # Check if the values were preserved
    if result["hotel_name"] == "Your Business Hotel":
        print("✅ Hotel name preserved correctly")
    else:
        print(f"❌ Hotel name not preserved: {result['hotel_name']}")
        
    if result["hotel_location"] == "New York, NY":
        print("✅ Hotel location preserved correctly")
    else:
        print(f"❌ Hotel location not preserved: {result['hotel_location']}")
        
    if result["current_adr"] == "$280":
        print("✅ Current ADR preserved correctly")
    else:
        print(f"❌ Current ADR not preserved: {result['current_adr']}")
    
    print("\n" + "="*80 + "\n")
    
    # Test 2: Natural language input
    print("=== Test 2: Natural Language Input ===")
    nl_input = "Optimize revenue for Seaside Resort in San Francisco, CA with luxury suites and standard rooms. Current occupancy is 85%, ADR $350, RevPAR $297.50, target RevPAR $320 for the next quarter."
    
    print("Input:")
    print(nl_input)
    
    result = nlp.process_input(nl_input)
    print("\nProcessed result:")
    print(json.dumps(result, indent=2))
    
    # Check if values were extracted
    if "Seaside Resort" in result["hotel_name"]:
        print("✅ Hotel name extracted correctly")
    else:
        print(f"❌ Hotel name not extracted correctly: {result['hotel_name']}")
        
    if "San Francisco" in result["hotel_location"]:
        print("✅ Hotel location extracted correctly")
    else:
        print(f"❌ Hotel location not extracted correctly: {result['hotel_location']}")

def test_main_input_processing():
    """Test how main.py processes inputs"""
    print("\n" + "="*80 + "\n")
    print("=== Test 3: Main.py Input Processing ===")
    
    # Simulate what happens in main.py
    payload = {
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
    
    print("Original payload:")
    print(json.dumps(payload, indent=2))
    
    # Simulate the processing in main.py
    nlp_processor = NLPProcessor()
    
    if payload:
        if isinstance(payload, str):
            inputs = nlp_processor.process_input(payload)
            print("\nProcessed as natural language")
        else:
            # This is the path that should be taken for dictionary input
            inputs = {
                'hotel_name': payload.get("hotel_name", "Grand Pacific Resort"),
                'hotel_location': payload.get("hotel_location", "Miami, FL"),
                'hotel_rating': payload.get("hotel_rating", "4.5"),
                'room_types': payload.get("room_types", "Standard, Deluxe, Suite"),
                'analysis_period': payload.get("analysis_period", "Next 90 days"),
                'forecast_period': payload.get("forecast_period", "Next 90 days"),
                'historical_occupancy': payload.get("historical_occupancy", "72%"),
                'current_adr': payload.get("current_adr", "$245"),
                'current_revpar': payload.get("current_revpar", "$176"),
                'target_revpar': payload.get("target_revpar", "$195"),
                'current_challenges': payload.get("current_challenges", "Weekday occupancy below target, OTA dependency")
            }
            print("\nProcessed as structured JSON")
    else:
        inputs = nlp_processor.defaults.copy()
        print("\nUsed defaults")
    
    print("\nFinal inputs:")
    print(json.dumps(inputs, indent=2))
    
    # Check if the values were preserved
    if inputs["hotel_name"] == "Your Business Hotel":
        print("✅ Hotel name preserved correctly in main.py processing")
    else:
        print(f"❌ Hotel name not preserved in main.py processing: {inputs['hotel_name']}")
        
    if inputs["hotel_location"] == "New York, NY":
        print("✅ Hotel location preserved correctly in main.py processing")
    else:
        print(f"❌ Hotel location not preserved in main.py processing: {inputs['hotel_location']}")

if __name__ == "__main__":
    test_nlp_processor()
    test_main_input_processing()
