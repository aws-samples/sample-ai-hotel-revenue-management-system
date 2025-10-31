#!/usr/bin/env python
"""
Test script for improved error handling with irrelevant queries and insufficient information.
"""

import json
from src.hotel_revenue_optimization.main import run

def test_irrelevant_queries():
    """Test with irrelevant queries that should be politely redirected"""
    
    irrelevant_queries = [
        {"prompt": "What's the weather like today?"},
        {"prompt": "Who won the election?"},
        {"prompt": "Tell me about the stock market"},
        {"prompt": "What's the latest news?"},
        {"prompt": "Can you help me book a hotel room?"},
        {"prompt": "Hello, how are you?"}
    ]
    
    print("=== Testing Irrelevant Queries ===\n")
    
    for i, query in enumerate(irrelevant_queries, 1):
        print(f"Test {i}: {query['prompt']}")
        response = run(query)
        
        print(f"Status: {response.get('status')}")
        print(f"Error Type: {response.get('error_type', 'N/A')}")
        print(f"Message: {response.get('message', 'N/A')}")
        
        if response.get('capabilities'):
            print("Capabilities shown: ✅")
        else:
            print("Capabilities shown: ❌")
        
        print("-" * 60)

def test_insufficient_information():
    """Test with hotel-related but insufficient information"""
    
    insufficient_queries = [
        {"prompt": "Help me increase RevPAR"},
        {"prompt": "I need hotel revenue optimization"},
        {"prompt": "My hotel needs better pricing"},
        {"prompt": "Optimize my property revenue"}
    ]
    
    print("\n=== Testing Insufficient Information ===\n")
    
    for i, query in enumerate(insufficient_queries, 1):
        print(f"Test {i}: {query['prompt']}")
        response = run(query)
        
        print(f"Status: {response.get('status')}")
        print(f"Error Type: {response.get('error_type', 'N/A')}")
        print(f"Message: {response.get('message', 'N/A')}")
        
        if response.get('required_info'):
            print("Required info shown: ✅")
            print(f"Examples provided: {len(response.get('examples', []))}")
        else:
            print("Required info shown: ❌")
        
        print("-" * 60)

def test_valid_query():
    """Test with a valid query to ensure it still works"""
    
    print("\n=== Testing Valid Query ===\n")
    
    valid_query = {"prompt": "Optimize revenue for Test Hotel in Miami with 70% occupancy and $200 ADR"}
    print(f"Test: {valid_query['prompt']}")
    
    response = run(valid_query)
    print(f"Status: {response.get('status')}")
    
    if response.get('status') == 'success':
        print("✅ Valid query processed successfully")
    else:
        print("❌ Valid query failed")
        print(f"Message: {response.get('message', 'N/A')}")

if __name__ == "__main__":
    test_irrelevant_queries()
    test_insufficient_information()
    test_valid_query()
