#!/usr/bin/env python3
import json
import subprocess

def test_mcp_tool():
    """Test the actual MCP tool call"""
    
    # Simple test payload
    payload = {
        "message": "Use PredictHQ to find 3 concerts in New York",
        "available_tools": ["predicthq-working___searchEvents"]
    }
    
    print("Testing MCP tool call...")
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        result = subprocess.run([
            'python', '-c', '''
import sys
sys.path.append("src")
from hotel_revenue_optimization.main import handler

payload = ''' + json.dumps(payload) + '''
result = handler(payload, None)
print("RESULT:", result)
'''
        ], capture_output=True, text=True, cwd='/Users/patilag/AgentCore/hotel_revenue_optimization')
        
        print(f"Exit code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mcp_tool()
