"""
Bedrock Converse wrapper for the models the crew uses (Amazon Nova and Anthropic Claude).

Current Nova and Claude text models are called through cross-region inference profiles, so this wrapper turns
the configured model ID ("bedrock/<base model id>") into an inference profile ID and calls the Converse API.
Errors are raised rather than returned as text, so a retired or misconfigured model fails loudly instead of
ending up inside a report.
"""

import os
from typing import Dict, Any, Optional, List

import boto3
from botocore.config import Config

# Prefixes of system-defined cross-region inference profiles
PROFILE_PREFIXES = ("us.", "eu.", "apac.", "jp.", "au.", "ca.", "us-gov.", "global.")
MAX_TOKENS = 8000


def _base_model_id(model_id: str) -> str:
    return model_id.removeprefix("bedrock/").removeprefix("converse/")


def to_inference_profile_id(model_id: str) -> str:
    """Return the inference profile ID (or ARN) to call for a configured model ID.

    "bedrock/amazon.nova-2-lite-v1:0" becomes "us.amazon.nova-2-lite-v1:0" with the default prefix. IDs that
    already carry a profile prefix, and ARNs (application inference profiles), are used as they are.
    """
    base = _base_model_id(model_id)
    if base.startswith("arn:") or base.startswith(PROFILE_PREFIXES):
        return base
    prefix = os.environ.get("BEDROCK_INFERENCE_PROFILE_PREFIX", "us").strip().rstrip(".")
    return f"{prefix}.{base}"


def inference_config_for(profile_id: str) -> Dict[str, Any]:
    """Inference settings per model family.

    Claude 5 models reject both temperature and top_p, so only maxTokens is sent to non-Nova models.
    """
    if "amazon.nova" in profile_id:
        return {"maxTokens": MAX_TOKENS, "temperature": 0.7, "topP": 0.9}
    return {"maxTokens": MAX_TOKENS}


def additional_fields_for(profile_id: str) -> Dict[str, Any]:
    """Model-specific request fields.

    Claude 5 models reason before they answer by default, and on long CrewAI prompts that reasoning can use the
    whole output budget, leaving no text. BEDROCK_CLAUDE_EFFORT (default "low"; also "medium" or "high") sets
    the effort level. Set it to an empty value for Claude models that reject the effort parameter
    (Claude Sonnet 4.5, Haiku 4.5 and earlier).
    """
    if "anthropic." in profile_id:
        effort = os.environ.get("BEDROCK_CLAUDE_EFFORT", "low").strip()
        if effort:
            return {"output_config": {"effort": effort}}
    return {}


class NovaModelWrapper:
    """Calls Bedrock models through the Converse API and cross-region inference profiles."""

    def __init__(self):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-west-2'),
            config=Config(
                connect_timeout=3600,  # 60 minutes
                read_timeout=3600,     # 60 minutes
                retries={'max_attempts': 3, 'mode': 'adaptive'}
            )
        )

    def requires_inference_profile(self, model_id: str) -> bool:
        """True for Bedrock Nova and Claude model IDs, which this wrapper calls through inference profiles."""
        base = _base_model_id(model_id)
        return base.startswith(("amazon.", "anthropic.", "arn:")) or base.startswith(PROFILE_PREFIXES)

    # Name used by earlier versions of this sample
    is_nova_model = requires_inference_profile

    def convert_to_nova_format(self, messages: List[Dict], system_prompt: Optional[str] = None,
                               profile_id: str = "") -> Dict[str, Any]:
        """Convert chat messages to a Converse request.

        Converse needs alternating user and assistant turns, so consecutive messages from the same role are
        merged and empty messages are dropped.
        """
        request: Dict[str, Any] = {"messages": [], "inferenceConfig": inference_config_for(profile_id)}
        extra_fields = additional_fields_for(profile_id)
        if extra_fields:
            request["additionalModelRequestFields"] = extra_fields

        if system_prompt:
            request["system"] = [{"text": system_prompt}]

        for msg in messages:
            content = msg.get('content')
            if isinstance(content, str):
                if not content.strip():
                    continue
                blocks = [{"text": content}]
            else:
                blocks = content or []
                if not blocks:
                    continue
            if request["messages"] and request["messages"][-1]["role"] == msg["role"]:
                request["messages"][-1]["content"].extend(blocks)
            else:
                request["messages"].append({"role": msg["role"], "content": list(blocks)})

        return request

    def invoke_nova_model(self, model_id: str, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        """Invoke a model through its inference profile and return the response text. Raises on failure."""
        profile_id = to_inference_profile_id(model_id)
        request_body = self.convert_to_nova_format(messages, system_prompt, profile_id)

        try:
            response = self.bedrock_client.converse(modelId=profile_id, **request_body)
        except Exception as e:
            raise RuntimeError(f"Bedrock call to {profile_id} failed: {e}") from e

        content = response.get('output', {}).get('message', {}).get('content', [])
        texts = [block['text'] for block in content if 'text' in block]
        if not texts:
            raise RuntimeError(f"Bedrock model {profile_id} returned no text (stopReason={response.get('stopReason')})")
        return "".join(texts)

    def get_fallback_model(self, failed_model: str) -> Optional[str]:
        """A different model to retry with: the active provider's tier4 model, or its tier3 model if that failed."""
        from .model_config import get_active_tiers

        tiers = get_active_tiers()
        for tier in ("tier4", "tier3"):
            candidate = tiers[tier][0]
            if to_inference_profile_id(candidate) != to_inference_profile_id(failed_model):
                return candidate
        return None


# Global instance
nova_wrapper = NovaModelWrapper()
