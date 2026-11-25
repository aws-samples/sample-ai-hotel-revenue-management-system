"""
Model configuration: the one place that names the Amazon Bedrock models the crew uses.

Each provider has four tiers and each agent is assigned a tier (DEFAULT_MODEL_ASSIGNMENTS below). Model IDs
are Bedrock base model IDs with LiteLLM's "bedrock/" prefix. The crew calls every model through a cross-region
inference profile, made by putting BEDROCK_INFERENCE_PROFILE_PREFIX in front of the base model ID
(see nova_model_wrapper.to_inference_profile_id).

Environment variables (all optional):
  MODEL_PROVIDER                    AMAZON (default), ANTHROPIC or HYBRID
  MODEL_TIER1 ... MODEL_TIER4       replace one tier's model for the active provider
  MODEL_<AGENT>                     replace one agent's model, for example MODEL_PRICING_STRATEGIST
  <AGENT>_LLM_TIER                  move one agent to another tier, for example PRICING_STRATEGIST_LLM_TIER=tier2
  BEDROCK_INFERENCE_PROFILE_PREFIX  inference profile geography: us (default), eu, apac or global
  BEDROCK_CLAUDE_EFFORT             Claude effort level: low (default), medium or high; empty to omit

To move to newer models, follow "Updating models and AWS package versions" in the README.
Last checked against `aws bedrock list-foundation-models` (ACTIVE models) on 2026-11-25.
"""

import os
from typing import Dict, List, Any, Optional

# Amazon Nova models: Nova 2 Lite is the current Nova text model; Nova Micro has no successor yet.
AMAZON_TIERS = {
    "tier1": ["bedrock/amazon.nova-2-lite-v1:0"],       # Complex reasoning
    "tier2": ["bedrock/amazon.nova-2-lite-v1:0"],       # Medium complexity - balanced performance
    "tier3": ["bedrock/amazon.nova-2-lite-v1:0"],       # Simple tasks - fast and cost-effective
    "tier4": ["bedrock/amazon.nova-micro-v1:0"]         # Basic tasks - fastest, lowest cost
}

# Anthropic Claude models
ANTHROPIC_TIERS = {
    "tier1": ["bedrock/anthropic.claude-sonnet-5-5"],   # Complex reasoning
    "tier2": ["bedrock/anthropic.claude-sonnet-5-5"],   # Medium complexity
    "tier3": ["bedrock/anthropic.claude-haiku-5-5"],    # Simple tasks - fast and capable
    "tier4": ["bedrock/anthropic.claude-haiku-5-5"]     # Basic tasks - cost-effective
}

# Provider selection - AMAZON (default), ANTHROPIC, or HYBRID (read again on every lookup)
ACTIVE_PROVIDER = os.environ.get("MODEL_PROVIDER", "AMAZON")

# Hybrid configuration - best of both providers
HYBRID_TIERS = {
    "tier1": ["bedrock/anthropic.claude-sonnet-5-5"],   # Claude for complex reasoning
    "tier2": ["bedrock/amazon.nova-2-lite-v1:0"],       # Nova for medium tasks
    "tier3": ["bedrock/amazon.nova-2-lite-v1:0"],       # Nova for simple tasks
    "tier4": ["bedrock/amazon.nova-micro-v1:0"]         # Nova for basic tasks
}

# Select active tier configuration
def get_active_tiers() -> Dict[str, List[str]]:
    """Get the active provider's tiers, with any MODEL_TIER1..MODEL_TIER4 overrides applied."""
    provider_map = {
        "AMAZON": AMAZON_TIERS,
        "ANTHROPIC": ANTHROPIC_TIERS,
        "HYBRID": HYBRID_TIERS
    }
    provider = os.environ.get("MODEL_PROVIDER", ACTIVE_PROVIDER).upper()
    tiers = {name: list(models) for name, models in provider_map.get(provider, AMAZON_TIERS).items()}
    for name in tiers:
        override = os.environ.get(f"MODEL_{name.upper()}")
        if override:
            tiers[name] = [override]
    return tiers

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
