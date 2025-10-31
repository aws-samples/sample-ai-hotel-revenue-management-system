#!/usr/bin/env python3
"""
Test script to validate timeout configurations
"""
import os
import sys
import time
from app import create_app
from app.api.agentcore import invoke_agentcore

def test_timeout_configuration():
    """Test timeout configuration and handling"""
    print("Testing timeout configuration...")
    
    # Create app with test configuration
    app = create_app('testing')
    
    with app.app_context():
        # Test payload
        test_payload = {
            "query_type": "natural_language",
            "query": "Test timeout handling for hotel pricing optimization"
        }
        
        print(f"AgentCore Timeout: {app.config.get('AGENTCORE_TIMEOUT', 'Not set')}s")
        print(f"AWS Connect Timeout: {app.config.get('AWS_CONNECT_TIMEOUT', 'Not set')}s")
        print(f"AWS Read Timeout: {app.config.get('AWS_READ_TIMEOUT', 'Not set')}s")
        
        start_time = time.time()
        
        try:
            result = invoke_agentcore(test_payload)
            duration = time.time() - start_time
            print(f"✅ Request completed in {duration:.2f}s")
            print(f"Response status: {result.get('status', 'unknown')}")
            print(f"Response summary: {result.get('summary', 'No summary')}")
            
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ Request failed after {duration:.2f}s")
            print(f"Error: {str(e)}")
            
            # Check if it's a timeout error
            if "timeout" in str(e).lower():
                print("✅ Timeout handling is working correctly")
            else:
                print("⚠️  Error is not timeout-related")

if __name__ == "__main__":
    test_timeout_configuration()
