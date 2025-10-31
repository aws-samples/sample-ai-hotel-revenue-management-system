#!/bin/bash
# Test script for the Hotel Revenue Optimization System with natural language prompts

# Set up environment
export AWS_PROFILE=${AWS_PROFILE:-default}
echo "Using AWS Profile: $AWS_PROFILE"

# Create output directory if it doesn't exist
mkdir -p output
chmod 777 output

# Function to test a single natural language prompt
test_prompt() {
    echo -e "\n\033[1;36m=== Testing Natural Language Prompt ===\033[0m"
    echo -e "\033[1;33mPrompt:\033[0m $1"
    echo -e "\033[1;35mProcessing...\033[0m"
    
    # Use agentcore invoke if available, otherwise use direct Python call
    if command -v agentcore &> /dev/null; then
        echo "Using agentcore CLI..."
        agentcore invoke --local "$1"
    else
        echo "Using direct Python call..."
        python -c "from src.hotel_revenue_optimization.main import run; import json; print(json.dumps(run('$1'), indent=2))"
    fi
}

# Function to run quick test
run_quick_test() {
    echo -e "\n\033[1;36m=== Running Quick Test ===\033[0m"
    echo "Testing with structured JSON input to verify the fix..."
    python quick_test.py
}

# Check if a specific prompt was provided
if [ "$1" ]; then
    if [ "$1" = "quick" ]; then
        run_quick_test
        exit 0
    else
        test_prompt "$1"
        exit 0
    fi
fi

# Sample prompts to test
echo -e "\033[1;32m=== Hotel Revenue Optimization System - Natural Language Testing ===\033[0m"
echo "This script will test the agent with various natural language prompts."
echo "You can also provide your own prompt as an argument to this script."
echo

# Menu of sample prompts
echo "Select a test option:"
echo "0) Quick test (verify the input processing fix)"
echo "1) Optimize revenue for Seaside Resort in Miami with standard and deluxe rooms, 75% occupancy, ADR $250"
echo "2) Forecast demand for a business hotel in New York for next quarter"
echo "3) Analyze competitor pricing for luxury hotels in Las Vegas"
echo "4) Optimize revenue for Mountain View Resort in Denver with 70% occupancy and $180 ADR"
echo "5) Create a pricing strategy for Beachfront Inn in San Diego for the next 45 days"
echo "6) Help me increase RevPAR (incomplete prompt)"
echo "7) Enter your own prompt"
echo "8) Run all sample prompts"
echo "9) Run comprehensive test suite"
echo "10) Exit"

read -p "Enter your choice (0-10): " choice

case $choice in
    0)
        run_quick_test
        ;;
    1)
        test_prompt "Optimize revenue for Seaside Resort in Miami, FL with standard and deluxe rooms. The hotel has a 4.5-star rating with current occupancy at 75%, ADR $250, RevPAR $187.50, and target RevPAR $200 for the next quarter. Current challenges include high cancellation rates and seasonal demand fluctuations."
        ;;
    2)
        test_prompt "Forecast demand for a business hotel in New York for next quarter"
        ;;
    3)
        test_prompt "Analyze competitor pricing for luxury hotels in Las Vegas"
        ;;
    4)
        test_prompt "Optimize revenue for Mountain View Resort in Denver with 70% occupancy and $180 ADR. We're struggling with weekday occupancy and OTA dependency."
        ;;
    5)
        test_prompt "Create a pricing strategy for Beachfront Inn in San Diego for the next 45 days"
        ;;
    6)
        test_prompt "Help me increase RevPAR"
        ;;
    7)
        echo "Enter your prompt:"
        read -p "> " custom_prompt
        test_prompt "$custom_prompt"
        ;;
    8)
        test_prompt "Optimize revenue for Seaside Resort in Miami, FL with standard and deluxe rooms. The hotel has a 4.5-star rating with current occupancy at 75%, ADR $250, RevPAR $187.50, and target RevPAR $200 for the next quarter. Current challenges include high cancellation rates and seasonal demand fluctuations."
        test_prompt "Forecast demand for a business hotel in New York for next quarter"
        test_prompt "Analyze competitor pricing for luxury hotels in Las Vegas"
        test_prompt "Optimize revenue for Mountain View Resort in Denver with 70% occupancy and $180 ADR. We're struggling with weekday occupancy and OTA dependency."
        test_prompt "Create a pricing strategy for Beachfront Inn in San Diego for the next 45 days"
        test_prompt "Help me increase RevPAR"
        ;;
    9)
        echo "Running comprehensive test suite..."
        python test_complete_system.py
        ;;
    10)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo -e "\n\033[1;32mTesting complete!\033[0m"
