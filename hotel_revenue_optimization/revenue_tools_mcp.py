"""
Enhanced revenue management tools with MCP Gateway integration
"""
from crewai_tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
from .best_practices_mcp import get_mcp_client

class BestPracticesSearchInput(BaseModel):
    """Input schema for best practices search"""
    query: str = Field(..., description="Search query for hotel revenue best practices")

class HotelBestPracticesSearchTool(BaseTool):
    """Tool for searching hotel revenue management best practices via AgentCore Gateway"""
    
    name: str = "search_hotel_best_practices"
    description: str = (
        "Search hotel revenue management best practices and optimization strategies. "
        "Use this tool to find industry best practices for pricing, revenue optimization, "
        "demand forecasting, and market analysis."
    )
    args_schema: Type[BaseModel] = BestPracticesSearchInput
    
    def _run(self, query: str) -> str:
        """Execute the best practices search"""
        try:
            # Check if MCP Gateway is configured
            gateway_url = os.getenv('AGENTCORE_GATEWAY_URL')
            if gateway_url:
                # Use MCP Gateway
                mcp_client = get_mcp_client()
                result = mcp_client.search_best_practices(query)
                
                if result["success"]:
                    data = result["data"]
                    if isinstance(data, dict) and "results" in data:
                        practices = []
                        for item in data["results"]:
                            content = item.get("content", "")
                            score = item.get("score", 0)
                            practices.append(f"• {content} (relevance: {score:.2f})")
                        
                        return f"Hotel Revenue Best Practices for '{query}':\n\n" + "\n".join(practices)
                    else:
                        return f"Best practices search completed for '{query}', but no structured results found."
                else:
                    # Fallback to embedded practices
                    return self._get_embedded_practices(query)
            else:
                # Fallback to embedded practices
                return self._get_embedded_practices(query)
                
        except Exception as e:
            # Fallback to embedded practices on any error
            return self._get_embedded_practices(query)
    
    def _get_embedded_practices(self, query: str) -> str:
        """Fallback to embedded best practices"""
        practices = {
            "adr": [
                "Monitor group vs transient mix for revenue optimization",
                "Track RevPAR, ADR, and occupancy daily with trend analysis",
                "Use machine learning algorithms for price optimization"
            ],
            "pricing": [
                "Implement dynamic pricing based on demand patterns",
                "Monitor competitor pricing and adjust rates accordingly",
                "Use length of stay restrictions to optimize revenue"
            ],
            "revenue": [
                "Focus on total revenue per available room (TRevPAR)",
                "Optimize channel mix to reduce distribution costs",
                "Implement upselling strategies at check-in"
            ],
            "demand": [
                "Analyze booking pace and adjust pricing proactively",
                "Use historical data to predict demand patterns",
                "Monitor local events and adjust inventory accordingly"
            ]
        }
        
        query_lower = query.lower()
        relevant_practices = []
        
        for category, items in practices.items():
            if category in query_lower or any(word in query_lower for word in ["revenue", "pricing", "optimization"]):
                relevant_practices.extend(items)
        
        if not relevant_practices:
            relevant_practices = practices["revenue"]  # Default to revenue practices
        
        return f"Hotel Revenue Best Practices for '{query}':\n\n" + "\n".join(f"• {practice}" for practice in relevant_practices[:5])
