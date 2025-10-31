#!/bin/bash
source .venv/bin/activate

# Disable OpenTelemetry
export OTEL_PYTHON_DISABLED=true
export OTEL_SDK_DISABLED=true

# Set AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Launch AgentCore locally
echo "Starting agent with OpenTelemetry disabled..."
agentcore launch --local
