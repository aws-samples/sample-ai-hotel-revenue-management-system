"""
Model configuration utility with provider-based tiers for easy switching.
"""

import os
from typing import Dict, List, Any, Optional

# Amazon Nova Models - AWS's latest multimodal models
AMAZON_TIERS = {
    "tier1": ["bedrock/amazon.nova-premier-v1:0"],      # Complex reasoning - highest capability
    "tier2": ["bedrock/amazon.nova-pro-v1:0"],          # Medium complexity - balanced performance
    "tier3": ["bedrock/amazon.nova-lite-v1:0"],         # Simple tasks - fast and cost-effective
    "tier4": ["bedrock/amazon.nova-micro-v1:0"]         # Basic tasks - ultra-fast
}

# Anthropic Claude Models - Advanced reasoning models
ANTHROPIC_TIERS = {
    "tier1": ["bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0"],      # Complex reasoning - with prompt caching
    "tier2": ["bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0"],      # Medium complexity - with prompt caching
    "tier3": ["bedrock/anthropic.claude-3-5-haiku-20241022-v1:0"],       # Simple tasks - fast and capable
    "tier4": ["bedrock/anthropic.claude-3-haiku-20240307-v1:0"]          # Basic tasks - cost-effective
}

# Provider selection - AMAZON (default), ANTHROPIC, or HYBRID
ACTIVE_PROVIDER = os.environ.get("MODEL_PROVIDER", "AMAZON")

# Hybrid configuration - best of both providers
HYBRID_TIERS = {
    "tier1": ["bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0"],      # Anthropic 3.7 for complex reasoning (with prompt caching)
    "tier2": ["bedrock/amazon.nova-pro-v1:0"],                           # Amazon for medium tasks
    "tier3": ["bedrock/amazon.nova-lite-v1:0"],                          # Amazon for simple tasks
    "tier4": ["bedrock/amazon.nova-micro-v1:0"]                          # Amazon for basic tasks
}

# Select active tier configuration
def get_active_tiers() -> Dict[str, List[str]]:
    """Get the active tier configuration based on provider selection."""
    provider_map = {
        "AMAZON": AMAZON_TIERS,
        "ANTHROPIC": ANTHROPIC_TIERS,
        "HYBRID": HYBRID_TIERS
    }
    return provider_map.get(ACTIVE_PROVIDER, AMAZON_TIERS)

# Current active tiers
MODEL_TIERS = get_active_tiers()

# Agent to tier mapping - business logic stays the same across providers
DEFAULT_MODEL_ASSIGNMENTS = {
    "market_analyst": "tier2",      # Medium complexity - market analysis
    "demand_forecaster": "tier2",   # Medium complexity - forecasting
    "pricing_strategist": "tier1",  # Complex reasoning - pricing strategy
    "revenue_manager": "tier2"      # Medium complexity - synthesis
}

def get_model_for_agent(agent_name: str) -> str:
    """Get the appropriate model for an agent based on active provider."""
    # Check for direct model override
    env_var_name = f"MODEL_{agent_name.upper()}"
    if env_var_name in os.environ:
        return os.environ[env_var_name]
    
    # Get tier assignment
    tier_name = os.environ.get(f"{agent_name.upper()}_LLM_TIER", 
                              DEFAULT_MODEL_ASSIGNMENTS.get(agent_name, "tier3"))
    
    # Get active tiers and return first model in tier
    active_tiers = get_active_tiers()
    tier_models = active_tiers.get(tier_name, active_tiers["tier3"])
    
    return tier_models[0]

def get_fallback_model(current_model: str, agent_name: str) -> Optional[str]:
    """Get fallback model within the same provider tier."""
    tier_name = os.environ.get(f"{agent_name.upper()}_LLM_TIER",
                              DEFAULT_MODEL_ASSIGNMENTS.get(agent_name, "tier3"))
    
    active_tiers = get_active_tiers()
    tier_models = active_tiers.get(tier_name, active_tiers["tier3"])
    
    try:
        current_index = tier_models.index(current_model)
        if current_index < len(tier_models) - 1:
            return tier_models[current_index + 1]
    except ValueError:
        return tier_models[0]
    
    # Cross-tier fallback within same provider
    if tier_name == "tier1":
        return active_tiers["tier2"][0]
    elif tier_name == "tier2":
        return active_tiers["tier3"][0]
    elif tier_name == "tier3":
        return active_tiers["tier4"][0]
    
    return None
