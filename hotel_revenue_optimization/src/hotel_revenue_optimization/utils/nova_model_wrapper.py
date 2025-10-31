"""
Nova Model Wrapper for handling Amazon Nova models alongside Anthropic models.
This wrapper provides compatibility for Nova models that may not be fully supported by LiteLLM yet.
"""

import os
import json
import boto3
from typing import Dict, Any, Optional, List
from botocore.config import Config

class NovaModelWrapper:
    """Wrapper to handle Nova models with direct Bedrock API calls when LiteLLM doesn't support them."""
    
    def __init__(self):
        # Configure boto3 client with extended timeout for Nova models
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-west-2'),
            config=Config(
                connect_timeout=3600,  # 60 minutes
                read_timeout=3600,     # 60 minutes
                retries={'max_attempts': 1}
            )
        )
    
    def is_nova_model(self, model_id: str) -> bool:
        """Check if the model requires inference profiles (Nova models or latest Claude models)."""
        return ('amazon.nova' in model_id or 
                'claude-sonnet-4' in model_id or 
                'claude-opus-4' in model_id or
                'claude-3-7-sonnet' in model_id)
    
    def convert_to_nova_format(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Convert standard chat format to Nova API format."""
        nova_request = {
            "messages": [],
            "inferenceConfig": {
                "maxTokens": 8000,  # Conservative increase from 4K to 8K
                "temperature": 0.7,
                "topP": 0.9
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            nova_request["system"] = [{"text": system_prompt}]
        
        # Convert messages to Nova format
        for msg in messages:
            if isinstance(msg.get('content'), str):
                # Simple string content
                nova_msg = {
                    "role": msg["role"],
                    "content": [{"text": msg["content"]}]
                }
            else:
                # Already in proper format
                nova_msg = msg
            
            nova_request["messages"].append(nova_msg)
        
        return nova_request
    
    def invoke_nova_model(self, model_id: str, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        """Invoke models that require inference profiles (Nova and latest Claude models)."""
        try:
            # Convert to proper format
            request_body = self.convert_to_nova_format(messages, system_prompt)
            
            # Map model IDs to inference profile IDs
            model_to_profile_map = {
                # Nova models
                'bedrock/amazon.nova-premier-v1:0': 'us.amazon.nova-premier-v1:0',
                'bedrock/amazon.nova-pro-v1:0': 'us.amazon.nova-pro-v1:0',
                'bedrock/amazon.nova-lite-v1:0': 'us.amazon.nova-lite-v1:0',
                'bedrock/amazon.nova-micro-v1:0': 'us.amazon.nova-micro-v1:0',
                # Latest Claude models requiring inference profiles
                'bedrock/anthropic.claude-sonnet-4-20250514-v1:0': 'us.anthropic.claude-sonnet-4-20250514-v1:0',
                'bedrock/anthropic.claude-opus-4-20250514-v1:0': 'us.anthropic.claude-opus-4-20250514-v1:0',
                'bedrock/anthropic.claude-opus-4-1-20250805-v1:0': 'us.anthropic.claude-opus-4-1-20250805-v1:0',
                'bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0': 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
            }
            
            # Get the inference profile ID
            profile_id = model_to_profile_map.get(model_id)
            if not profile_id:
                return f"Error: No inference profile found for model {model_id}"
            
            # Make the API call using inference profile
            response = self.bedrock_client.converse(
                modelId=profile_id,
                **request_body
            )
            
            # Extract text from response
            if 'output' in response and 'message' in response['output']:
                content = response['output']['message'].get('content', [])
                if content and 'text' in content[0]:
                    return content[0]['text']
            
            return "Error: No valid response from model"
            
        except Exception as e:
            return f"Error invoking model: {str(e)}"
    
    def get_fallback_model(self, failed_model: str) -> Optional[str]:
        """Get a fallback model when Nova model fails."""
        # Map Nova models to Claude equivalents
        nova_to_claude_map = {
            'amazon.nova-premier-v1:0': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'amazon.nova-pro-v1:0': 'anthropic.claude-3-5-haiku-20241022-v1:0',
            'amazon.nova-lite-v1:0': 'anthropic.claude-3-haiku-20240307-v1:0',
            'amazon.nova-micro-v1:0': 'amazon.titan-text-express-v1'
        }
        
        clean_model = failed_model.replace('bedrock/', '')
        fallback = nova_to_claude_map.get(clean_model)
        return f"bedrock/{fallback}" if fallback else None

# Global instance
nova_wrapper = NovaModelWrapper()
