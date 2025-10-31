"""
Custom LLM class that handles Nova models by intercepting them before LiteLLM processing.
"""

from crewai.llm import LLM
from typing import Any, Dict, List, Optional
from .nova_model_wrapper import nova_wrapper

class NovaCompatibleLLM(LLM):
    """Custom LLM class that handles Nova models alongside standard LiteLLM models."""
    
    def __init__(self, model: str, **kwargs):
        self.original_model = model
        
        # Check if this is a Nova model
        if nova_wrapper.is_nova_model(model):
            # For Nova models, we'll handle them specially
            self.is_nova = True
            self.nova_model_id = model
            # Use a Claude model as the base for LiteLLM compatibility
            fallback_model = nova_wrapper.get_fallback_model(model)
            super().__init__(model=fallback_model or "bedrock/anthropic.claude-3-haiku-20240307-v1:0", **kwargs)
        else:
            # Standard models go through LiteLLM normally
            self.is_nova = False
            super().__init__(model=model, **kwargs)
    
    def call(self, messages: List[Dict], **kwargs) -> str:
        """Override call method to handle Nova models."""
        if self.is_nova:
            # Extract system prompt if present
            system_prompt = None
            user_messages = []
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                else:
                    user_messages.append(msg)
            
            # Use Nova wrapper for direct API call
            try:
                return nova_wrapper.invoke_nova_model(
                    self.nova_model_id, 
                    user_messages, 
                    system_prompt
                )
            except Exception as e:
                # Fall back to standard LiteLLM if Nova fails
                print(f"Nova model failed, falling back to Claude: {e}")
                return super().call(messages, **kwargs)
        else:
            # Standard LiteLLM processing
            return super().call(messages, **kwargs)

def create_llm_for_model(model_id: str) -> LLM:
    """Factory function to create appropriate LLM instance."""
    return NovaCompatibleLLM(model=model_id)
