import json
import logging
import time
import uuid
import boto3
import requests
from datetime import datetime
from flask import current_app
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError, ConnectTimeoutError, ReadTimeoutError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler if it doesn't exist
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

def invoke_agentcore(payload, session_id=None):
    """
    Invoke the AgentCore endpoint with IAM authentication and timeout handling
    
    Args:
        payload (dict): The payload to send to the AgentCore endpoint
        session_id (str): Optional session ID for AgentCore
        
    Returns:
        dict: The response from the AgentCore endpoint
    """
    # Start timing the request
    start_time = time.time()
    
    # Get the AgentCore runtime ARN from the app config
    agent_runtime_arn = current_app.config.get('AGENTCORE_RUNTIME_ARN')
    if not agent_runtime_arn:
        raise Exception("AGENTCORE_RUNTIME_ARN not configured")
    
    # Extract query type
    query_type = payload.get("query_type", "unknown")
    
    # Log the request details
    logger.info(f"Invoking AgentCore with payload type: {query_type}")
    logger.info(f"AgentCore Runtime ARN: {agent_runtime_arn}")
    
    logger.info("Attempting to use boto3 client for AgentCore invocation")
    # Get the region from the app config
    region = current_app.config.get('AWS_REGION', 'us-west-2')
    logger.info(f"Using AWS region: {region}")
    
    # Get timeout configurations
    connect_timeout = current_app.config.get('AWS_CONNECT_TIMEOUT', 10)
    read_timeout = current_app.config.get('AWS_READ_TIMEOUT', 120)
    agentcore_timeout = current_app.config.get('AGENTCORE_TIMEOUT', 120)
    
    logger.info(f"Timeout settings - Connect: {connect_timeout}s, Read: {read_timeout}s, AgentCore: {agentcore_timeout}s")
    
    # Configure boto3 with timeouts
    boto_config = BotoConfig(
        connect_timeout=connect_timeout,
        read_timeout=read_timeout,
        retries={'max_attempts': 2, 'mode': 'standard'}
    )
    
    # Initialize the Bedrock AgentCore client with timeout configuration
    agent_core_client = boto3.client(
        'bedrock-agentcore', 
        region_name=region,
        config=boto_config
    )
    
    # Prepare the payload
    # Format the payload as expected by AgentCore
    if query_type == "natural_language":
        input_text = json.dumps({"prompt": payload.get("query", "")}).encode()
    else:
        # For structured form, convert to a natural language prompt
        hotel_type = payload.get("hotel_type", "")
        location = payload.get("location", "")
        season = payload.get("season", "")
        star_rating = payload.get("star_rating", "")
        occupancy_rate = payload.get("occupancy_rate", "")
        
        prompt = f"Optimize revenue for a {star_rating}-star {hotel_type} hotel in {location} during {season} season with current occupancy rate of {occupancy_rate}%"
        input_text = json.dumps({"prompt": prompt}).encode()
    
    logger.info(f"Prepared payload for AgentCore: {input_text.decode()}")
    
    # Use provided session ID or generate a new one
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Invoke the agent runtime with timeout handling
    logger.info(f"Invoking AgentCore runtime with {agentcore_timeout}s timeout")
    
    try:
        response = agent_core_client.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            runtimeSessionId=session_id,
            payload=input_text
        )
        logger.info(f"Received response from AgentCore")
    except (ConnectTimeoutError, ReadTimeoutError) as timeout_error:
        logger.error(f"Timeout error invoking AgentCore: {str(timeout_error)}")
        raise Exception(f"AgentCore request timed out after {agentcore_timeout} seconds")
    except ClientError as client_error:
        error_code = client_error.response.get('Error', {}).get('Code', 'Unknown')
        error_message = client_error.response.get('Error', {}).get('Message', str(client_error))
        logger.error(f"AWS Client Error ({error_code}): {error_message}")
        raise Exception(f"AgentCore API error: {error_message}")
    except Exception as invoke_error:
        logger.error(f"Unexpected error invoking AgentCore: {str(invoke_error)}")
        raise
    
    # Process the response
    response_content = ""
    if "text/event-stream" in response.get("contentType", ""):
        # Handle streaming response
        content = []
        for line in response["response"].iter_lines(chunk_size=10):
            if line:
                line = line.decode("utf-8")
                if line.startswith("data: "):
                    line = line[6:]
                    content.append(line)
        response_content = "\n".join(content)
        logger.info(f"Processed streaming response, length: {len(response_content)}")
    
    elif response.get("contentType") == "application/json":
        # Handle standard JSON response
        content = []
        for chunk in response.get("response", []):
            content.append(chunk.decode('utf-8'))
        response_content = ''.join(content)
        logger.info(f"Processed JSON response, length: {len(response_content)}")
        
        # Try to parse as JSON
        try:
            response_json = json.loads(response_content)
            if isinstance(response_json, dict) and "response" in response_json:
                response_content = response_json["response"]
        except:
            pass
    
    else:
        # Handle other response types
        if 'response' in response:
            response_obj = response['response']
            if hasattr(response_obj, 'read') and callable(response_obj.read):
                response_content = response_obj.read().decode('utf-8')
            else:
                response_content = str(response_obj)
        else:
            response_content = str(response)
        
    logger.info(f"Response content preview: {response_content[:200]}...")  # Log first 200 chars
    
    # Try to parse the response content as JSON to extract the report
    try:
        response_json = json.loads(response_content)
        if isinstance(response_json, dict):
            # Check if there's a report field in the JSON
            if "report" in response_json:
                logger.info("Found 'report' field in response JSON")
                markdown_content = response_json["report"]
                status = response_json.get("status", "success")
                completed_tasks = response_json.get("completed_tasks", [])
                failed_tasks = response_json.get("failed_tasks", [])
                
                # Create a formatted response with the extracted report
                response_data = {
                    "summary": "Revenue optimization recommendations",
                    "markdown_content": markdown_content,
                    "status": status,
                    "completed_tasks": completed_tasks,
                    "failed_tasks": failed_tasks
                }
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                logger.info(f"Request completed in {duration_ms:.2f}ms")
                
                return response_data
    except Exception as json_e:
        logger.warning(f"Failed to parse response as JSON or extract report: {str(json_e)}")
    
    # If we couldn't extract a report, use the full response as markdown content
    response_data = {
        "summary": "Response from AgentCore",
        "markdown_content": response_content,
        "status": "success",
        "completed_tasks": ["agent_invocation"],
        "failed_tasks": []
    }
    
    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"Request completed in {duration_ms:.2f}ms")
    
    return response_data
