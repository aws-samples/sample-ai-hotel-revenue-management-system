# OpenTelemetry Integration for Hotel Revenue Optimization

This document describes the OpenTelemetry integration implemented for the Hotel Revenue Optimization project using AWS Distro for OpenTelemetry (ADOT) for GenAI.

## Overview

The OpenTelemetry integration provides:

1. **Distributed Tracing**: Track operations across the entire system
2. **GenAI-specific Metrics**: Monitor model invocations, latency, token usage, etc.
3. **Structured Logging**: Console logs in JSON format for easy parsing
4. **Error Tracking**: Comprehensive error tracking with stack traces
5. **Partial Results Handling**: Graceful handling of failures with partial results

## AWS Distro for OpenTelemetry (ADOT) for GenAI

This project uses AWS Distro for OpenTelemetry (ADOT) for GenAI, which provides:

1. **GenAI-specific Tracing**: Special spans for model invocations
2. **GenAI-specific Metrics**: Metrics for model usage, latency, etc.
3. **AWS Integration**: Easy integration with AWS services like CloudWatch
4. **Resource Detection**: Automatic detection of AWS resources

## Key Components

### 1. GenAI Tracer

The `GenAITracer` is used to create spans specifically for model invocations:

```python
span = genai_tracer.start_span(
    name="MODEL_INVOKE",
    model=model_name,
    attributes={
        "agent.name": agent_name,
        "operation.id": operation_id
    }
)
```

### 2. GenAI Metrics

The `GenAIMetrics` is used to record metrics for model invocations:

```python
# Record model invocation start
genai_metrics.record_model_invocation_start(model_name)

# Record model invocation success
genai_metrics.record_model_invocation_success(
    model_name=model_name,
    latency_ms=duration * 1000,
    input_tokens=input_tokens,
    output_tokens=output_tokens
)

# Record model invocation failure
genai_metrics.record_model_invocation_failure(
    model_name=model_name,
    error_type=error_type,
    latency_ms=duration * 1000
)
```

### 3. JSON Console Logging

All logs are output to the console in JSON format for easy parsing:

```json
{
  "timestamp": "2025-07-21T02:15:30.123456Z",
  "level": "INFO",
  "message": "MODEL_INVOKE STARTED | Agent: pricing_strategist | Model: anthropic.claude-3-sonnet-20240229-v1:0",
  "logger": "HotelRevenueOptimization",
  "event_type": "MODEL_INVOKE",
  "status": "started",
  "agent": "pricing_strategist",
  "model": "anthropic.claude-3-sonnet-20240229-v1:0",
  "operation_id": "550e8400-e29b-41d4-a716-446655440001",
  "task": "pricing_strategy_task",
  "crew": "HotelRevenueOptimizationCrew",
  "prompt_length": 1024,
  "system_prompt_length": 256,
  "temperature": 0.7,
  "max_tokens": 4096,
  "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
  "fallback_attempts": 0
}
```

## Configuration

The OpenTelemetry integration can be configured with the following environment variables:

- `OTEL_SERVICE_NAME`: Service name (defaults to "hotel-revenue-optimization")
- `OTEL_SERVICE_VERSION`: Service version (defaults to "1.0.0")
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OTLP exporter endpoint
- `OTEL_EXPORTER_OTLP_PROTOCOL`: OTLP exporter protocol (grpc or http/protobuf)
- `DEPLOYMENT_ENVIRONMENT`: Deployment environment (development, staging, production)

## Span Attributes

The following attributes are added to spans:

### Common Attributes

- `agent.name`: Name of the agent
- `model.name`: Name of the model
- `operation.id`: Unique identifier for the operation
- `operation.type`: Type of operation (e.g., "MODEL_INVOKE", "TASK_EXECUTION")
- `task.name`: Name of the task (if applicable)
- `crew.name`: Name of the crew (if applicable)

### Model Invocation Attributes

- `prompt_length`: Length of the prompt
- `system_prompt_length`: Length of the system prompt
- `temperature`: Temperature for generation
- `max_tokens`: Maximum tokens to generate
- `model_id`: Model ID
- `fallback_attempts`: Number of fallback attempts

### Result Attributes

- `result.response_length`: Length of the response
- `result.estimated_input_tokens`: Estimated number of input tokens
- `result.estimated_output_tokens`: Estimated number of output tokens
- `result.total_input_tokens`: Total number of input tokens
- `result.total_output_tokens`: Total number of output tokens
- `result.model_used`: Model used
- `result.fallback_attempts`: Number of fallback attempts

### Error Attributes

- `error.type`: Type of error
- `error.message`: Error message
- `error_detail_error_code`: Error code
- `error_detail_error_message`: Error message
- `error_detail_attempts`: Number of attempts
- `error_detail_model_id`: Model ID

## Response Schema for Partial Results

When some tasks fail but others complete successfully, the system returns a response with partial results:

```json
{
  "status": "partial_success",
  "completed_tasks": ["market_analysis_task", "demand_forecast_task"],
  "failed_tasks": ["pricing_strategy_task", "revenue_management_task"],
  "results": {
    "market_analysis_task": {
      "output": "Market analysis report content..."
    },
    "demand_forecast_task": {
      "output": "Demand forecast report content..."
    },
    "pricing_strategy_task": {
      "placeholder": "Task pricing_strategy_task failed to complete",
      "error": "Model invocation failed after multiple retries",
      "error_details": {
        "error_code": "ThrottlingException",
        "retry_attempts": 5,
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
      }
    },
    "revenue_management_task": {
      "placeholder": "Task revenue_management_task failed to complete",
      "error": "Task dependency failed",
      "error_details": {
        "failed_dependency": "pricing_strategy_task"
      }
    }
  },
  "metadata": {
    "run_id": "550e8400-e29b-41d4-a716-446655440001",
    "start_time": "2025-07-21T02:23:45Z",
    "end_time": "2025-07-21T02:24:35Z",
    "duration_seconds": 50.2,
    "performance": {
      "task_durations": {
        "market_analysis_task": 15.8,
        "demand_forecast_task": 19.2,
        "pricing_strategy_task": 15.2
      },
      "model_latencies": {
        "anthropic.claude-3-haiku-20240307-v1:0": 2.5,
        "anthropic.claude-3-sonnet-20240229-v1:0": 3.3
      }
    }
  },
  "report": "# Hotel Revenue Optimization Plan\n\n## Executive Summary\n..."
}
```

## Usage in UI Applications

When building UI applications that consume the API:

1. Check the `status` field to determine if all tasks completed successfully
2. Display results from `completed_tasks` normally
3. For `failed_tasks`, display placeholders with error information
4. Use the `metadata` for performance monitoring and debugging

## Viewing Traces and Metrics

Traces and metrics can be viewed in:

1. **AWS CloudWatch**: If running in AWS
2. **Jaeger**: For local development
3. **Prometheus**: For metrics
4. **Grafana**: For visualization

To view traces locally, you can run Jaeger:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

Then open http://localhost:16686 in your browser.
