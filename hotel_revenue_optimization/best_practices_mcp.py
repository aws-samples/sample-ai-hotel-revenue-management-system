"""
MCP integration for hotel best practices search via AgentCore Gateway
"""
import requests
import json
from typing import Dict, Any, List
import os

class HotelBestPracticesMCP:
    """MCP client for hotel best practices search via AgentCore Gateway"""
    
    def __init__(self, gateway_url: str, auth_token: str = None):
        """
        Initialize MCP client for AgentCore Gateway
        
        Args:
            gateway_url: AgentCore Gateway MCP endpoint URL
            auth_token: OAuth token for authentication (if required)
        """
        self.gateway_url = gateway_url
        self.auth_token = auth_token
        self.headers = {
            'Content-Type': 'application/json'
        }
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
    
    def search_best_practices(self, query: str) -> Dict[str, Any]:
        """
        Search hotel revenue management best practices
        
        Args:
            query: Search query for best practices
            
        Returns:
            Dictionary with search results
        """
        try:
            # MCP tool call payload
            payload = {
                "method": "tools/call",
                "params": {
                    "name": "search_hotel_best_practices",
                    "arguments": {
                        "query": query
                    }
                }
            }
            
            response = requests.post(
                self.gateway_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": result.get("result", {}),
                    "query": query
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "query": query
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def list_available_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools from the Gateway
        
        Returns:
            List of available tools
        """
        try:
            payload = {
                "method": "tools/list",
                "params": {}
            }
            
            response = requests.post(
                self.gateway_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("result", {}).get("tools", [])
            else:
                return []
                
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []

# Environment-based configuration
def get_mcp_client() -> HotelBestPracticesMCP:
    """
    Get configured MCP client from environment variables
    
    Environment variables:
    - AGENTCORE_GATEWAY_URL: Gateway MCP endpoint URL
    - AGENTCORE_AUTH_TOKEN: OAuth token (optional)
    """
    gateway_url = os.getenv('AGENTCORE_GATEWAY_URL')
    auth_token = os.getenv('AGENTCORE_AUTH_TOKEN')
    
    if not gateway_url:
        raise ValueError("AGENTCORE_GATEWAY_URL environment variable is required")
    
    return HotelBestPracticesMCP(gateway_url, auth_token)
