#!/bin/bash
source .venv/bin/activate

# Set agent name and ID
export AGENT_NAME="hotel_revenue_optimization"
export AGENT_ID="${AGENT_NAME}-local"

# AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2
export AWS_LOG_GROUP="/aws/bedrock-agentcore/runtimes/${AGENT_ID}"

# OpenTelemetry environment variables
export AGENT_OBSERVABILITY_ENABLED=true
export OTEL_PYTHON_DISTRO=aws_distro
export OTEL_RESOURCE_ATTRIBUTES="service.name=${AGENT_NAME},aws.log.group.names=${AWS_LOG_GROUP}"
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=${AWS_LOG_GROUP},x-aws-log-stream=runtime-logs,x-aws-metric-namespace=bedrock-agentcore"

# Optional: Disable OpenTelemetry if needed
# export OTEL_PYTHON_DISABLED=true

# Launch AgentCore locally
echo "Starting agent with observability enabled..."
agentcore launch --local
