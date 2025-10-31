#!/usr/bin/env python
"""
Test script for the Hotel Revenue Optimization System with natural language prompts.
This script demonstrates how to invoke the agent with different types of natural language inputs.
"""

import sys
import json
import os
from src.hotel_revenue_optimization.main import run
from src.hotel_revenue_optimization.utils.nlp_processor import NLPProcessor

def print_separator():
    print("\n" + "="*80 + "\n")

def test_natural_language_prompts():
    """Test the agent with various natural language prompts."""
    
    # Sample natural language prompts
    prompts = [
        # Complete prompt with all information
        "Optimize revenue for Seaside Resort in Miami, FL with standard and deluxe rooms. " +
        "The hotel has a 4.5-star rating with current occupancy at 75%, ADR $250, RevPAR $187.50, " +
        "and target RevPAR $200 for the next quarter. Current challenges include high cancellation rates " +
        "and seasonal demand fluctuations.",
        
        # Prompt with minimal information
        "Forecast demand for a business hotel in New York for next quarter",
        
        # Prompt focusing on competitor analysis
        "Analyze competitor pricing for luxury hotels in Las Vegas",
        
        # Prompt focusing on specific challenges
        "Optimize revenue for Mountain View Resort in Denver with 70% occupancy and $180 ADR. " +
        "We're struggling with weekday occupancy and OTA dependency.",
        
        # Prompt with unusual time period
        "Create a pricing strategy for Beachfront Inn in San Diego for the next 45 days",
        
        # Prompt with incomplete information
        "Help me increase RevPAR"
    ]
    
    # Process each prompt
    for i, prompt in enumerate(prompts):
        print(f"Test {i+1}: {prompt}")
        print_separator()
        
        # First, show what the NLP processor extracts
        nlp = NLPProcessor()
        extracted = nlp.process_input(prompt)
        print("NLP Processor extracted:")
        print(json.dumps(extracted, indent=2))
        print_separator()
        
        # Then run the actual agent
        print("Agent response:")
        response = run(prompt)
        
        # Print status and any error messages
        if isinstance(response, dict) and "status" in response:
            print(f"Status: {response['status']}")
            
            if response["status"] == "error":
                print("\nError message:")
                print(response["message"])
                print("\nMissing fields:")
                print(", ".join(response["missing_fields"]))
                print("\nGuidance:")
                print(response["guidance"])
            else:
                print("\nAgent completed successfully!")
                
                # Check if there's a report
                if "report" in response:
                    report_preview = response["report"][:500] + "..." if len(response["report"]) > 500 else response["report"]
                    print("\nReport preview:")
                    print(report_preview)
        else:
            print("Unexpected response format")
            print(response)
        
        print_separator()
        input("Press Enter to continue to the next test...")
        print_separator()

if __name__ == "__main__":
    test_natural_language_prompts()
