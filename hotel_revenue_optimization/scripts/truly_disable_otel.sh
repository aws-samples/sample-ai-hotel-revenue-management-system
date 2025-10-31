#!/bin/bash
source .venv/bin/activate

# Completely disable OpenTelemetry
export OTEL_SDK_DISABLED=true
export OTEL_PYTHON_DISABLED=true
export OTEL_TRACES_EXPORTER=none
export OTEL_METRICS_EXPORTER=none
export OTEL_LOGS_EXPORTER=none

# Set AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Launch AgentCore locally with OpenTelemetry completely disabled
echo "Launching AgentCore locally with OpenTelemetry completely disabled..."
agentcore launch --local
