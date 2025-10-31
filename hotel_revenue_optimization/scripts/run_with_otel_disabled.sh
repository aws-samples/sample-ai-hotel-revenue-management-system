#!/bin/bash
source .venv/bin/activate

# Disable OpenTelemetry
export OTEL_SDK_DISABLED=true

# Set AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2
export AWS_PROFILE=genai

# Launch AgentCore with OpenTelemetry disabled
echo "Launching AgentCore with OTEL_SDK_DISABLED=true..."
agentcore launch
