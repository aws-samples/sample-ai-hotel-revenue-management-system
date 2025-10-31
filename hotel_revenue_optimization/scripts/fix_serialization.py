#!/usr/bin/env python
import json
import sys
from fastapi.responses import JSONResponse

# Add the project root to the Python path
sys.path.append('.')

from src.hotel_revenue_optimization.main import run

def make_serializable(obj):
    """Convert non-serializable objects to serializable format."""
    if hasattr(obj, 'dict') and callable(obj.dict):
        # Handle Pydantic models
        return obj.dict()
    elif hasattr(obj, 'model_dump') and callable(obj.model_dump):
        # Handle Pydantic v2 models
        return obj.model_dump()
    elif hasattr(obj, 'json') and callable(obj.json):
        # Handle objects with json method
        return json.loads(obj.json())
    elif hasattr(obj, '__dict__'):
        # Handle generic objects
        return {k: make_serializable(v) for k, v in obj.__dict__.items() 
                if not k.startswith('_')}
    elif isinstance(obj, (list, tuple)):
        # Handle lists and tuples
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        # Handle dictionaries
        return {k: make_serializable(v) for k, v in obj.items()}
    else:
        # Convert to string as last resort
        try:
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)

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
    
    # Fix the result by making it serializable
    print("Attempting to fix serialization...")
    serializable_result = make_serializable(result)
    
    # Try to serialize the fixed result
    try:
        json_result = json.dumps(serializable_result)
        print(f"Fixed JSON serialization successful")
        
        # Save the fixed result to a file
        with open("fixed_response.json", "w") as f:
            json.dump(serializable_result, f, indent=2)
        print("Fixed response saved to fixed_response.json")
    except TypeError as e:
        print(f"Fixed JSON serialization failed: {e}")
