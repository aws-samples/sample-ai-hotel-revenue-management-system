# Hotel Revenue Optimization - Performance Monitoring

This directory contains utilities for performance monitoring, logging, and model management in the Hotel Revenue Optimization system.

## Overview

The performance monitoring system provides:

1. **Detailed Logging**: Track all operations, including model calls, task execution, and crew activities
2. **Performance Metrics**: Measure response times, token usage, and other performance indicators
3. **Rate Limit Handling**: Automatically handle rate limits with exponential backoff and model fallbacks
4. **Model Management**: Dynamically select and fallback between models based on availability and requirements
5. **Analysis Tools**: Generate reports and visualizations of system performance

## Components

### Logger (`logger.py`)

The `PerformanceLogger` class provides structured logging for all system operations:

- **Operation Tracking**: Start and end timing for operations like model calls and task execution
- **Event Logging**: Record system events like crew initialization and rate limits
- **JSON Output**: Store logs in structured JSON format for easy analysis

### Model Wrapper (`model_wrapper.py`)

The `BedrockModelWrapper` class wraps Bedrock model calls with:

- **Performance Tracking**: Measure response times and token usage
- **Rate Limit Handling**: Implement exponential backoff with jitter
- **Model Fallbacks**: Automatically switch to fallback models when rate limited
- **Error Handling**: Properly handle and log various error conditions

### Model Configuration (`model_config.py`)

The `model_config.py` module provides:

- **Model Tiers**: Define tiers of models with fallback options
- **Dynamic Selection**: Select models based on agent requirements and environment variables
- **Fallback Strategy**: Provide fallback models when primary models are unavailable

### Analysis Tools (`analyze_logs.py`)

The `analyze_logs.py` script provides:

- **Log Analysis**: Parse and analyze performance logs
- **Report Generation**: Create markdown reports with performance metrics
- **Visualizations**: Generate charts of model and task performance
- **Recommendations**: Suggest optimizations based on performance data

## Usage

### Environment Variables

Configure model selection and logging with environment variables:

```
# Model assignments
MODEL_MARKET_ANALYST=bedrock/anthropic.claude-3-haiku-20240307-v1:0
MODEL_DEMAND_FORECASTER=bedrock/anthropic.claude-3-haiku-20240307-v1:0
MODEL_PRICING_STRATEGIST=bedrock/anthropic.claude-3-sonnet-20240229-v1:0
MODEL_REVENUE_MANAGER=bedrock/anthropic.claude-3-haiku-20240307-v1:0

# Tier assignments (tier1=opus, tier2=sonnet, tier3=haiku, tier4=instant)
TIER_MARKET_ANALYST=tier3
TIER_DEMAND_FORECASTER=tier3
TIER_PRICING_STRATEGIST=tier2
TIER_REVENUE_MANAGER=tier3

# Logging configuration
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_LOGGING=true
```

### Analyzing Logs

After running the system, analyze the logs with:

```bash
python -m src.hotel_revenue_optimization.utils.analyze_logs output/logs/performance_20250720_235959.json
```

This will generate a report in `output/reports/` with performance metrics and recommendations.

## Extending

### Adding New Models

To add new models to the system:

1. Update the `MODEL_TIERS` dictionary in `model_config.py`
2. Add appropriate handling in `model_wrapper.py` if the model requires special formatting

### Adding New Metrics

To track additional metrics:

1. Update the `start_operation` and `end_operation` methods in `logger.py`
2. Add analysis for the new metrics in `analyze_logs.py`

## Troubleshooting

### Rate Limiting Issues

If you encounter rate limiting issues:

1. Check the logs for `RATE_LIMIT` events
2. Consider adjusting the tier assignments to use smaller models
3. Increase the backoff parameters in `model_wrapper.py`
4. Request quota increases from AWS for the affected models

### Performance Issues

If the system is running slowly:

1. Generate a performance report with `analyze_logs.py`
2. Identify the slowest models and tasks
3. Consider using smaller models for less critical tasks
4. Adjust the process from sequential to parallel if appropriate
