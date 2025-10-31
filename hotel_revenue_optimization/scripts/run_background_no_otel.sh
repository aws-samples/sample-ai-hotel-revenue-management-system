#!/bin/bash
source .venv/bin/activate

# Disable OpenTelemetry
export OTEL_PYTHON_DISABLED=true

# Set AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Launch AgentCore locally in the background
nohup agentcore launch --local > app_output.log 2>&1 &

echo "Application started in the background. Process ID: $!"
echo "You can check the logs with: tail -f app_output.log"
