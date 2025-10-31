#!/bin/bash
source .venv/bin/activate

# Set OpenTelemetry environment variables
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_PROTOCOL=grpc
export OTEL_SERVICE_NAME=hotel_revenue_optimization
export OTEL_TRACES_SAMPLER=always_on
export OTEL_LOGS_EXPORTER=otlp
export OTEL_METRICS_EXPORTER=otlp
export OTEL_RESOURCE_ATTRIBUTES=service.name=hotel_revenue_optimization,service.version=1.0.0

# Set AWS environment variables
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Launch AgentCore locally with OpenTelemetry instrumentation
OTEL_PYTHON_DISABLED=false opentelemetry-instrument agentcore launch --local
