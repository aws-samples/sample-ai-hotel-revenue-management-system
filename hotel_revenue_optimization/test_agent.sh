#!/bin/bash

# Hotel Revenue Optimization System - Test Script
# This script tests the deployed agent with a sample hotel

set -e  # Exit on error

# Default values
LOCAL_MODE="false"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --local)
      LOCAL_MODE="true"
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --local       Test locally deployed agent"
      echo "  --help        Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "=== Testing Hotel Revenue Optimization System ==="
echo "Local Mode: $LOCAL_MODE"
echo "=================================================="

# Sample hotel data
HOTEL_DATA='{
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
}'

# Create output directory if it doesn't exist
mkdir -p output

# Run the test
if [ "$LOCAL_MODE" == "true" ]; then
  echo "Testing locally deployed agent..."
  agentcore invoke --local "$HOTEL_DATA" | tee output/test_result_local.json
else
  echo "Testing AWS deployed agent..."
  agentcore invoke "$HOTEL_DATA" | tee output/test_result_aws.json
fi

echo "Test complete! Results saved to output directory."
