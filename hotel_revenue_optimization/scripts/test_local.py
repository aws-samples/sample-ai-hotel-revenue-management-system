#!/usr/bin/env python
import os
import json
import sys

# Add the project root to the Python path
sys.path.append('.')

from src.hotel_revenue_optimization.main import run

# Set environment variables
os.environ["OTEL_SDK_DISABLED"] = "true"

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

# Print the result
print(json.dumps(result, indent=2))
