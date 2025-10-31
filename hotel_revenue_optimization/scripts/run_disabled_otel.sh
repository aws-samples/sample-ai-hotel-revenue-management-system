#!/bin/bash
source .venv/bin/activate

# Disable OpenTelemetry with the specific environment variable
export OTEL_SDK_DISABLED=true

# Launch AgentCore locally
echo "Starting agent with OTEL_SDK_DISABLED=true..."
agentcore launch --local
