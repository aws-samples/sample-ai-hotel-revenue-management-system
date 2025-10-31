import time
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError
import json
import random

from .observability import observability
from .model_config import get_model_for_agent, get_fallback_model, MODEL_TIERS
from .nova_model_wrapper import nova_wrapper

class BedrockModelWrapper:
    """
    Wrapper for Bedrock models to track performance and handle rate limiting
    """
    
    def __init__(self, 
                 model_id: str, 
                 agent_name: str, 
                 max_retries: int = 5, 
                 base_delay: float = 1.0,
                 max_delay: float = 60.0):
        """
        Initialize the model wrapper
        
        Args:
            model_id: The Bedrock model ID
            agent_name: The name of the agent using this model
            max_retries: Maximum number of retries for rate limiting
            base_delay: Base delay for exponential backoff (seconds)
            max_delay: Maximum delay for exponential backoff (seconds)
        """
        self.model_id = model_id
        self.agent_name = agent_name
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        
        # Extract the model name from the model ID
        self.model_name = model_id.split('/')[-1] if '/' in model_id else model_id
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.environ.get('AWS_REGION', 'us-west-2')
        )
        
        # Track total tokens and costs
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        
        # Track fallbacks
        self.fallback_attempts = 0
        self.current_model_id = model_id
        
    def invoke(self, 
               prompt: str, 
               system_prompt: Optional[str] = None, 
               temperature: float = 0.7,
               max_tokens: int = 4096,
               operation_type: str = "MODEL_INVOKE",
               task_name: Optional[str] = None,
               crew_name: Optional[str] = "HotelRevenueOptimizationCrew") -> Dict[str, Any]:
        """
        Invoke the model with retry logic for rate limiting
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            operation_type: Type of operation for logging
            task_name: Optional name of the task being executed
            crew_name: Optional name of the crew
            
        Returns:
            The model response
        """
        operation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log the operation start
        observability.log_event(
            event_type=operation_type,
            agent_name=self.agent_name,
            model_name=self.model_name,
            details={
                "operation_id": operation_id,
                "prompt_length": len(prompt),
                "system_prompt_length": len(system_prompt) if system_prompt else 0,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model_id": self.current_model_id,
                "fallback_attempts": self.fallback_attempts
            },
            task_name=task_name,
            crew_name=crew_name
        )
        
        # Prepare the request body based on the model provider
        if "anthropic" in self.current_model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            if system_prompt:
                body["system"] = system_prompt
        else:
            # Default format for other models
            body = {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            if system_prompt:
                body["system_prompt"] = system_prompt
        
        # Convert the request body to JSON
        body_json = json.dumps(body)
        
        # Implement retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                # Invoke the model
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.current_model_id,
                    body=body_json
                )
                
                # Parse the response
                response_body = json.loads(response.get('body').read())
                
                # Extract the response text based on the model provider
                if "anthropic" in self.current_model_id:
                    response_text = response_body.get('content', [{}])[0].get('text', '')
                    
                    # Estimate token usage (this is approximate)
                    input_tokens = len(prompt) // 4  # Rough estimate
                    output_tokens = len(response_text) // 4  # Rough estimate
                else:
                    response_text = response_body.get('text', '')
                    
                    # Estimate token usage (this is approximate)
                    input_tokens = len(prompt) // 4  # Rough estimate
                    output_tokens = len(response_text) // 4  # Rough estimate
                
                # Update token counts
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log the operation completion
                observability.log_event(
                    event_type=f"{operation_type}_COMPLETE",
                    agent_name=self.agent_name,
                    model_name=self.model_name,
                    details={
                        "operation_id": operation_id,
                        "duration_seconds": duration,
                        "response_length": len(response_text),
                        "estimated_input_tokens": input_tokens,
                        "estimated_output_tokens": output_tokens,
                        "total_input_tokens": self.total_input_tokens,
                        "total_output_tokens": self.total_output_tokens,
                        "model_used": self.current_model_id,
                        "fallback_attempts": self.fallback_attempts,
                        "status": "completed"
                    },
                    task_name=task_name,
                    crew_name=crew_name
                )
                
                return {
                    "text": response_text,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "model_used": self.current_model_id
                }
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                error_message = e.response.get('Error', {}).get('Message', '')
                
                # Handle rate limiting errors
                if (error_code == 'ThrottlingException' or 
                    'TooManyRequests' in error_message or 
                    'rate' in error_message.lower() or
                    error_code == '429'):
                    
                    # Always try to get a fallback model first
                    fallback_model = get_fallback_model(self.current_model_id, self.agent_name)
                    
                    if fallback_model and self.fallback_attempts < 3:  # Allow up to 3 fallbacks
                        # Switch to fallback model
                        self.current_model_id = fallback_model
                        self.fallback_attempts += 1
                        
                        observability.log_event(
                            event_type="MODEL_FALLBACK",
                            agent_name=self.agent_name,
                            model_name=self.model_name,
                            details={
                                "operation_id": operation_id,
                                "original_model": self.model_id,
                                "fallback_model": fallback_model,
                                "fallback_attempt": self.fallback_attempts,
                                "error_code": error_code,
                                "error_message": error_message,
                                "task_name": task_name,
                                "crew_name": crew_name
                            }
                        )
                        
                        # Try again immediately with the fallback model
                        continue
                    
                    # Calculate backoff time with jitter
                    delay = min(self.max_delay, self.base_delay * (2 ** attempt))
                    delay = delay * (0.5 + random.random())  # Add jitter
                    
                    observability.log_event(
                        event_type="RATE_LIMIT",
                        agent_name=self.agent_name,
                        model_name=self.model_name,
                        details={
                            "operation_id": operation_id,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries,
                            "delay": delay,
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": self.current_model_id
                        },
                        task_name=task_name,
                        crew_name=crew_name
                    )
                    
                    # Wait before retrying
                    time.sleep(delay)
                    
                    # If this is the last attempt, try one more fallback to a lower tier model
                    if attempt == self.max_retries - 1:
                        # Try to get an emergency fallback model
                        emergency_model = self._get_emergency_fallback(self.agent_name)
                        
                        if emergency_model and self.current_model_id != emergency_model:
                            self.current_model_id = emergency_model
                            self.fallback_attempts += 1
                            
                            observability.log_event(
                                event_type="EMERGENCY_MODEL_FALLBACK",
                                agent_name=self.agent_name,
                                model_name=self.model_name,
                                details={
                                    "operation_id": operation_id,
                                    "original_model": self.model_id,
                                    "fallback_model": emergency_model,
                                    "fallback_attempt": self.fallback_attempts,
                                    "error_code": error_code,
                                    "error_message": error_message
                                },
                                task_name=task_name,
                                crew_name=crew_name
                            )
                            
                            # Try one more time with the emergency fallback model
                            continue
                        
                        # If we're already using the lowest tier model, log and raise
                        observability.log_exception(
                            exception=e,
                            agent_name=self.agent_name,
                            model_name=self.model_name,
                            details={
                                "operation_id": operation_id,
                                "error_code": error_code,
                                "error_message": error_message,
                                "attempts": self.max_retries,
                                "model_id": self.current_model_id,
                                "duration_seconds": time.time() - start_time,
                                "fallback_attempts": self.fallback_attempts
                            },
                            task_name=task_name,
                            crew_name=crew_name
                        )
                        raise
                else:
                    # For other errors, log and raise immediately
                    observability.log_exception(
                        exception=e,
                        agent_name=self.agent_name,
                        model_name=self.model_name,
                        details={
                            "operation_id": operation_id,
                            "error_code": error_code,
                            "error_message": error_message,
                            "model_id": self.current_model_id,
                            "task_name": task_name,
                            "crew_name": crew_name,
                            "duration_seconds": time.time() - start_time
                        }
                    )
                    raise
        
        # This should not be reached due to the raise in the loop
        return {"text": "", "input_tokens": 0, "output_tokens": 0}
    def _get_emergency_fallback(self, agent_name: str) -> Optional[str]:
        """
        Get an emergency fallback model when all tier options are exhausted.
        This will try to find the most efficient model that can still handle the task.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Emergency fallback model ID or None if no fallback is available
        """
        # Get the current tier for this agent
        current_tier = os.environ.get(f"TIER_{agent_name.upper()}", 
                                     DEFAULT_MODEL_ASSIGNMENTS.get(agent_name, "tier3"))
        
        # Try to get a model from a lower tier
        if current_tier == "tier1":
            return MODEL_TIERS["tier2"][0]
        elif current_tier == "tier2":
            return MODEL_TIERS["tier3"][0]
        elif current_tier == "tier3":
            return MODEL_TIERS["tier4"][0]
        elif current_tier == "tier4":
            # If we're already at the lowest tier, use the most efficient model
            return MODEL_TIERS["tier4"][-1]  # Last model in tier4 (most efficient)
        
        # Default emergency fallback
        return "bedrock/amazon.titan-text-express-v1"
