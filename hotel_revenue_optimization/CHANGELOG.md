# Changelog

All notable changes to the Hotel Revenue Optimization System will be documented in this file.

## [2.1.0] - 2025-09-23

### Added
- **Provider-Based Model Architecture**: Clean separation of model providers (AMAZON, ANTHROPIC, HYBRID)
- **Amazon Nova Model Support**: Full integration with Nova Premier, Pro, Lite, and Micro models
- **Inference Profile Support**: Proper handling of models requiring inference profiles (Nova and latest Claude models)
- **Enhanced Observability**: Comprehensive task tracking and performance metrics
- **Clean Response Format**: Removed empty results, added DEBUG-level task logging

### Changed
- **Default Provider**: AMAZON (Nova models) for optimal speed/cost balance
- **Model Configuration**: Provider-based tiers instead of mixed model fallbacks
- **Performance Optimization**: 45s execution time with Amazon Nova models
- **Claude 3.7 Sonnet**: Updated to use Claude 3.7 with prompt caching for ANTHROPIC provider

### Performance Benchmarks
- **AMAZON Provider**: 45 seconds (fastest, most cost-effective)
- **HYBRID Provider**: 83 seconds (balanced speed and quality)  
- **ANTHROPIC Provider**: 238 seconds (highest quality, detailed analysis)

### Fixed
- **Task Duration Logic**: Removed artificial task duration calculations
- **Observability Tracking**: Proper task completion and failure tracking
- **Model Wrapper**: Enhanced Nova model wrapper with inference profile mapping

## [2.0.0] - 2025-07-24

### Added
- **Enhanced Input Processing**: Multi-format input support (prompt, message, structured JSON)
- **Natural Language Processing**: Extract hotel information from free-form text
- **Intelligent Error Handling**: Detect irrelevant queries, booking requests, insufficient information
- **Comprehensive Testing**: Validated with multiple test scenarios and edge cases

### Fixed
- **Critical Input Processing Bug**: System now generates hotel-specific reports instead of hardcoded Miami responses
- **Crew Integration**: Corrected crew execution flow for proper input processing
- **Dynamic Hotel Analysis**: Proper integration with CrewAI framework for dynamic analysis

### Changed
- **Production Deployment**: Successfully deployed to AWS Bedrock AgentCore
- **Agent ARN**: `arn:aws:bedrock-agentcore:us-west-2:943562114123:runtime/hotel_revenue_optimization-2OYNqEGtl3`
- **Status**: Production-ready and fully operational

## [1.0.0] - 2025-06-15

### Added
- **Initial Release**: Hotel Revenue Optimization System with CrewAI and Amazon Bedrock
- **Multi-Agent Architecture**: Market Analyst, Demand Forecaster, Pricing Strategist, Revenue Manager
- **Claude Model Integration**: Support for Claude 3 Opus, Sonnet, and Haiku models
- **Comprehensive Reporting**: Detailed revenue optimization plans with implementation timelines
- **Performance Monitoring**: Basic logging and metrics collection

### Features
- **Revenue Analysis**: Current performance analysis with gap identification
- **Pricing Strategy**: Dynamic pricing recommendations and implementation plans
- **Risk Assessment**: Comprehensive risk factors and mitigation strategies
- **KPI Tracking**: Primary and secondary performance metrics
- **Financial Projections**: Revenue impact analysis with confidence levels
