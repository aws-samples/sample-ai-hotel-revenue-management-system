#!/usr/bin/env python3
import requests
import json

def test_gateway_target():
    """Test existing gateway target directly"""
    
    gateway_url = "https://gateway-predicthq-gateway.bedrock-agentcore.us-east-1.amazonaws.com"
    
    # Test the working target from conversation summary
    payload = {
        "method": "tools/call",
        "params": {
            "name": "predicthq-working___searchEvents",
            "arguments": {
                "limit": 3
            }
        }
    }
    
    print("🔍 Testing existing gateway target...")
    print(f"URL: {gateway_url}/mcp")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{gateway_url}/mcp",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"\n📊 Status: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.text:
            try:
                data = response.json()
                print(f"✅ Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📄 Raw Response: {response.text}")
        else:
            print("⚠️  Empty response")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gateway_target()
