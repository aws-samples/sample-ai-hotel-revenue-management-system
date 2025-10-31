#!/bin/bash
source .venv/bin/activate

# Disable OpenTelemetry
export OTEL_SDK_DISABLED=true

# Launch AgentCore locally in the background
nohup agentcore launch --local > app_output.log 2>&1 &

echo "Application started in the background with OTEL_SDK_DISABLED=true. Process ID: $!"
echo "You can check the logs with: tail -f app_output.log"
echo "Waiting 30 seconds for the application to start..."
sleep 30
echo "Application should be ready now at http://localhost:8080"
