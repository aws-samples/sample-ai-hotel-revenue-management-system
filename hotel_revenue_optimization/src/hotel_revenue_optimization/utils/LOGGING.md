# Enhanced Logging System for Hotel Revenue Optimization

This document describes the enhanced logging system implemented for the Hotel Revenue Optimization project, including OpenTelemetry integration and partial results handling.

## Overview

The enhanced logging system provides:

1. **Structured Logging**: Detailed, structured logs for all major events
2. **OpenTelemetry Integration**: Distributed tracing for performance monitoring
3. **Partial Results Handling**: Graceful handling of failures with partial results
4. **Error Tracking**: Comprehensive error logging with stack traces
5. **Performance Metrics**: Tracking of model calls, task execution times, and more

## Log Levels

The system uses the following log levels:

- **INFO**: Major events like task starts/completions, model invocations, crew operations
- **WARNING**: Non-critical issues that might need attention
- **ERROR**: Failures that impact functionality but don't stop execution
- **DEBUG**: Detailed debugging information (disabled by default)

## Major Events Logged

The following major events are logged at INFO level:

1. **Crew Events**:
   - `CREW_INIT`: Crew initialization
   - `CREW_START`: Crew execution start
   - `CREW_INPUTS`: Input parameters for the crew
   - `CREW_COMPLETE`: Crew execution completion

2. **Agent Events**:
   - `AGENT_INIT`: Agent initialization

3. **Task Events**:
   - `TASK_INIT`: Task initialization
   - `TASK_EXECUTION STARTED`: Task execution start
   - `TASK_EXECUTION COMPLETED`: Task execution completion

4. **Model Events**:
   - `MODEL_INVOKE STARTED`: Model invocation start
   - `MODEL_INVOKE COMPLETED`: Model invocation completion
   - `MODEL_FALLBACK`: Model fallback due to rate limiting
   - `RATE_LIMIT`: Rate limiting encountered

5. **System Events**:
   - `RUN_START`: System run start
   - `INPUTS_PROCESSED`: Input parameters processed
   - `RUN_COMPLETE`: System run completion

## Log Structure

Each log entry includes the following information:

- **Event Type**: Type of event (e.g., `TASK_EXECUTION`, `MODEL_INVOKE`)
- **Status**: Status of the event (e.g., `started`, `completed`, `failed`)
- **Agent**: Name of the agent involved
- **Model**: Name of the model being used
- **Task**: Name of the task being executed (if applicable)
- **Crew**: Name of the crew (if applicable)
- **Duration**: Duration of the operation in seconds (for completion events)
- **Details**: Additional details specific to the event

Example log entry:
```
2025-07-21 02:15:30 - HotelRevenueOptimization - INFO - MODEL_INVOKE STARTED | Agent: pricing_strategist | Model: anthropic.claude-3-sonnet-20240229-v1:0 | Task: pricing_strategy_task | Crew: HotelRevenueOptimizationCrew
```

## OpenTelemetry Integration

The system integrates with OpenTelemetry for distributed tracing:

1. **Spans**: Each operation creates a span with appropriate attributes
2. **Trace Context**: Trace context is propagated across operations
3. **Span Attributes**: Spans include attributes for agent, model, task, etc.
4. **Error Tracking**: Errors are recorded in spans with stack traces

To enable OpenTelemetry export, set the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

## Partial Results Handling

When some tasks fail but others complete successfully, the system:

1. Continues execution where possible
2. Collects results from successful tasks
3. Creates placeholders for failed tasks
4. Returns a response with partial results
5. Includes error details for failed tasks

## Response Schema

The system returns responses in the following format:

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

For the full JSON schema, see `src/hotel_revenue_optimization/schemas/response_schema.json`.

## Configuration

The logging system can be configured with the following environment variables:

- `LOG_LEVEL`: Logging level (INFO, WARNING, ERROR, DEBUG)
- `ENABLE_PERFORMANCE_LOGGING`: Enable/disable performance logging (true/false)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry exporter endpoint
- `OTEL_SERVICE_NAME`: OpenTelemetry service name (defaults to "hotel-revenue-optimization")

## Usage in UI Applications

When building UI applications that consume the API:

1. Check the `status` field to determine if all tasks completed successfully
2. Display results from `completed_tasks` normally
3. For `failed_tasks`, display placeholders with error information
4. Use the `metadata` for performance monitoring and debugging

## Error Handling

The system provides detailed error information:

1. **Error Message**: Human-readable error message
2. **Error Details**: Additional details about the error
3. **Stack Trace**: Stack trace for debugging (in logs only)
4. **Error Location**: Where the error occurred
5. **Error Type**: Type of error (e.g., `ThrottlingException`, `ValueError`)

## Performance Analysis

After running the system, analyze the logs with:

```bash
python -m src.hotel_revenue_optimization.utils.analyze_logs output/logs/performance_<timestamp>.json
```

This will generate a report with:

- Model performance metrics
- Task execution times
- Rate limiting events
- Optimization recommendations
