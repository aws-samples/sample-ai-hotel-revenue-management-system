"""
CrewAI LLM that sends Bedrock models (Amazon Nova and Anthropic Claude) through the Converse wrapper.
"""

import logging
from typing import Dict, List, Union

from crewai.llm import LLM

from .nova_model_wrapper import nova_wrapper, to_inference_profile_id

logger = logging.getLogger(__name__)


class NovaCompatibleLLM(LLM):
    """LLM that calls Bedrock models through inference profiles, retrying once on a fallback model."""

    def __init__(self, model: str, **kwargs):
        self.original_model = model

        if nova_wrapper.requires_inference_profile(model):
            self.is_nova = True
            self.nova_model_id = model
            self.fallback_model_id = nova_wrapper.get_fallback_model(model)
            # CrewAI keeps this name for bookkeeping; requests go through call() below
            super().__init__(model=f"bedrock/{to_inference_profile_id(model)}", **kwargs)
        else:
            # Other models go through LiteLLM normally
            self.is_nova = False
            super().__init__(model=model, **kwargs)

    def supports_function_calling(self) -> bool:
        """The Converse wrapper sends plain chat turns without tools, so CrewAI must not force tool calls.

        With this False, CrewAI builds structured outputs (such as the planning step's plan) through call()
        and text instructions, instead of a forced tool_choice, which Claude 5 models reject.
        """
        if self.is_nova:
            return False
        return super().supports_function_calling()

    def call(self, messages: Union[str, List[Dict]], **kwargs) -> str:
        """Send the conversation to Bedrock; on failure retry once with the fallback model."""
        if not self.is_nova:
            return super().call(messages, **kwargs)

        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        system_parts = []
        chat_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system_parts.append(msg.get('content', ''))
            else:
                chat_messages.append(msg)
        system_prompt = "\n\n".join(part for part in system_parts if part) or None

        try:
            return nova_wrapper.invoke_nova_model(self.nova_model_id, chat_messages, system_prompt)
        except Exception as primary_error:
            if not self.fallback_model_id:
                raise
            logger.warning("Model %s failed (%s); retrying with fallback model %s",
                           self.nova_model_id, primary_error, self.fallback_model_id)
            return nova_wrapper.invoke_nova_model(self.fallback_model_id, chat_messages, system_prompt)


def create_llm_for_model(model_id: str) -> LLM:
    """Factory function to create appropriate LLM instance."""
    return NovaCompatibleLLM(model=model_id)
