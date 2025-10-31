#!/usr/bin/env python
import json
import sys

# Add the project root to the Python path
sys.path.append('.')

from src.hotel_revenue_optimization.main import run

# Test payload
payload = {
    "hotel_name": "Grand Pacific Resort",
    "hotel_location": "Miami, FL",
    "hotel_rating": "4.5",
    "room_types": "Standard, Deluxe, Suite",
    "analysis_period": "Next 90 days",
    "forecast_period": "Next 90 days",
    "historical_occupancy": "72%",
    "current_adr": "$245",
    "current_revpar": "$176",
    "target_revpar": "$195",
    "current_challenges": "Weekday occupancy below target, OTA dependency"
}

# Run the application
result = run(payload)

# Print the result type
print(f"Result type: {type(result)}")

# Try to serialize the result to JSON
try:
    json_result = json.dumps(result)
    print(f"JSON serialization successful")
except TypeError as e:
    print(f"JSON serialization failed: {e}")
    
    # Try to fix the result by creating a simple response
    simple_response = {
        "status": "success",
        "message": "Hotel revenue optimization completed",
        "hotel_name": payload["hotel_name"],
        "hotel_location": payload["hotel_location"]
    }
    
    # Try to serialize the simple response
    try:
        json_result = json.dumps(simple_response)
        print(f"Simple JSON serialization successful")
    except TypeError as e:
        print(f"Simple JSON serialization failed: {e}")
