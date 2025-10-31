# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel Revenue Optimization System is a multi-agent AI solution using CrewAI and Amazon Bedrock AgentCore. Four specialized agents collaborate to optimize hotel pricing: Market Analyst, Demand Forecaster, Pricing Strategist, and Revenue Manager.

**Status**: Production-ready v2.1.0 deployed to AWS Bedrock AgentCore

## Common Commands

### Local Development

```bash
# Run with default settings
python -m src.hotel_revenue_optimization.main

# Run test suite
python test_complete_system.py           # Full system test with structured JSON
python test_natural_language.py          # NLP and prompt format testing
python test_error_handling.py            # Error handling validation
python test_input_processing.py          # Input format verification
```

### AgentCore Deployment

```bash
# Initial setup (one-time)
agentcore configure --entrypoint src/hotel_revenue_optimization/main.py \
  --name hotel_revenue_optimization --execution-role BedrockAgentCoreRole --region us-east-1

# Deployment workflow
./build.sh --region us-east-1 --profile <your-profile>              # Build configuration
./deploy.sh --region us-east-1 --profile <your-profile> --aws       # Deploy to AWS
agentcore launch                                                     # Launch runtime

# Local testing workflow
./deploy.sh --region us-east-1 --profile <your-profile> --local     # Deploy locally
agentcore launch --local                                             # Launch local runtime

# Invocation examples
agentcore invoke '{"prompt": "Analyze revenue for The Grand Hotel in Chicago. Current ADR $200, occupancy 70%."}'
agentcore invoke --local '{"hotel_name": "Test Hotel", "hotel_location": "Miami, FL", "current_adr": "$280"}'
```

### Docker Workflow

```bash
# Build image
docker build -t bedrock_agentcore-hotel_revenue_optimization .

# Run container with environment variables
docker run -d -p 8080:8080 \
  -e DISABLE_AUTH=true \
  -e AWS_REGION=us-east-1 \
  -e MODEL_PROVIDER=AMAZON \
  -e AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id --profile $AWS_PROFILE) \
  -e AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key --profile $AWS_PROFILE) \
  -v $(pwd)/output:/app/output \
  --name bedrock_agentcore-hotel bedrock_agentcore-hotel_revenue_optimization:latest

# Test container API
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Optimize revenue for Test Hotel in Miami"}'

# View container logs
docker logs -f bedrock_agentcore-hotel
```

## High-Level Architecture

### Core Components

**Entry Point**: `src/hotel_revenue_optimization/main.py`
- AgentCore entrypoint decorated with `@app.entrypoint`
- Multi-format input processing: structured JSON, natural language prompts, message format
- NLP extraction via `NLPProcessor` from `utils/nlp_processor.py`
- Error detection: irrelevant queries, booking requests, insufficient information
- Returns JSON response with revenue optimization report or structured error

**Crew Orchestration**: `src/hotel_revenue_optimization/crew.py`
- CrewAI crew managing four specialized agents with task dependencies
- Task execution: Market Analysis & Demand Forecast (parallel) → Pricing Strategy → Revenue Management
- Observability tracking via `utils/observability.py` (CREW_INIT, TASK_COMPLETE, performance metrics)
- Dynamic model assignment via `get_model_for_agent()` from `utils/model_config.py`

**Model Configuration**: `src/hotel_revenue_optimization/utils/model_config.py`
- Provider-based architecture: AMAZON (default), ANTHROPIC, or HYBRID
- Four-tier system: tier1 (complex reasoning) → tier4 (basic tasks)
- Environment variable `MODEL_PROVIDER` controls all assignments
- Agent tiers: pricing_strategist=tier1, market_analyst=tier2, demand_forecaster=tier2, revenue_manager=tier2
- Per-agent overrides: `MODEL_{AGENT}_OVERRIDE` or `{AGENT}_LLM_TIER` environment variables

### Multi-Agent Architecture

Four specialized agents working in sequence:

1. **Market Analyst** (tier2): Analyzes market trends, competitor pricing, external demand factors
2. **Demand Forecaster** (tier2): Predicts future demand, booking pace, occupancy patterns
3. **Pricing Strategist** (tier1 - most complex): Develops optimal pricing strategies, rate adjustments
4. **Revenue Manager** (tier2): Creates comprehensive revenue plan, executive summary, KPIs

Task flow:
- Market Analysis + Demand Forecast run in parallel (no dependencies)
- Pricing Strategy depends on both Market Analysis and Demand Forecast
- Revenue Management depends on all three prior tasks

### Model Provider System

**AMAZON Provider** (Default - Production Recommended):
- tier1: amazon.nova-premier-v1:0 (complex reasoning)
- tier2: amazon.nova-pro-v1:0 (medium complexity)
- tier3: amazon.nova-lite-v1:0 (simple tasks)
- tier4: amazon.nova-micro-v1:0 (basic tasks)

**ANTHROPIC Provider** (Quality-Focused):
- tier1/tier2: anthropic.claude-3-7-sonnet-20250219-v1:0 (with prompt caching)
- tier3: anthropic.claude-3-5-haiku-20241022-v1:0
- tier4: anthropic.claude-3-haiku-20240307-v1:0

**HYBRID Provider** (Balanced):
- tier1: Claude 3.7 Sonnet (complex reasoning)
- tier2-tier4: Amazon Nova models (speed/cost)

Switch providers via environment variable:
```bash
MODEL_PROVIDER=AMAZON    # Default
MODEL_PROVIDER=ANTHROPIC # Highest quality
MODEL_PROVIDER=HYBRID    # Balanced
```

### Input Processing

The system accepts three input formats:

1. **Structured JSON** (programmatic):
```json
{
  "hotel_name": "The Ritz-Carlton",
  "hotel_location": "San Francisco, CA",
  "current_adr": "$450",
  "historical_occupancy": "68%"
}
```

2. **Prompt format** (chat UI):
```json
{
  "prompt": "Analyze revenue for The Ritz-Carlton in San Francisco. Current ADR $450, occupancy 68%."
}
```

3. **Message format** (messaging platforms):
```json
{
  "message": "Help me optimize revenue for my boutique hotel in Miami. 120 rooms, ADR $280, occupancy 65%."
}
```

**NLP Processing** (`src/hotel_revenue_optimization/utils/nlp_processor.py`):
- Extracts hotel information from natural language
- Validates hotel relevance with keyword detection
- Returns structured error responses for irrelevant queries, booking requests, or insufficient information

### Configuration and Output

**Agent Configs**: `src/hotel_revenue_optimization/config/agents.yaml`
- YAML definitions: role, goal, backstory, verbose flag, default llm
- Models dynamically assigned from environment variables at runtime

**Task Configs**: `src/hotel_revenue_optimization/config/tasks_optimized.yaml`
- Task descriptions with placeholders: {hotel_name}, {hotel_location}, {current_adr}, etc.
- Falls back to `tasks.yaml` if optimized version not found
- Defines task dependencies via `context` parameter

**Output Location**: `output/revenue_optimization_plan.md`
- Final markdown report generated by Revenue Manager agent
- Comprehensive report: market analysis, demand forecast, pricing strategy, revenue plan
- System ensures `output/` directory exists before execution

### Utilities System

Located in `src/hotel_revenue_optimization/utils/`:
- `observability.py`: Central event logging (CREW_INIT, TASK_COMPLETE, performance metrics)
- `nlp_processor.py`: Natural language extraction with keyword detection
- `model_config.py`: Provider-based model tier system
- `model_wrapper.py`: Bedrock API calls with retry logic and rate limit handling
- `nova_llm.py`: LLM instance creation for Amazon Nova models
- `markdown_formatter.py`: Final report formatting

### Tools System

Located in `src/hotel_revenue_optimization/tools/`:
- `market_tools.py`: Market analysis and competitor pricing tools
- `demand_tools.py`: Demand forecasting and booking pace tools
- `pricing_tools.py`: Pricing strategy and optimization tools
- `revenue_tools.py`: Revenue management and KPI tracking tools

Each tool provides CrewAI-compatible functions that agents can invoke during task execution.

## Development Patterns

### Adding a New Agent

1. **Define agent**: Add configuration to `config/agents.yaml` (role, goal, backstory, llm)
2. **Define task**: Add to `config/tasks_optimized.yaml` with description and placeholders
3. **Create agent method** in `crew.py`:
   - Call `get_model_for_agent("agent_name")` for model ID
   - Use `create_llm_for_model(model_id)` to create LLM instance
   - Log with `observability.log_event(event_type="AGENT_INIT", ...)`
4. **Create task method** in `crew.py`:
   - Format description with `.format(**inputs)`
   - Set dependencies via `context=[other_task1, other_task2]`
   - Log TASK_INIT and TASK_COMPLETE events
5. **Update crew() method**: Add agent and task to lists
6. **Add tier assignment**: Update `DEFAULT_MODEL_ASSIGNMENTS` in `model_config.py` if needed

### Modifying Model Assignments

**Environment variables** (preferred, set in `.env`):
```bash
# Switch provider (affects all agents)
MODEL_PROVIDER=AMAZON          # or ANTHROPIC or HYBRID

# Change specific agent tier
PRICING_STRATEGIST_LLM_TIER=tier2

# Override specific agent model completely
MODEL_PRICING_STRATEGIST=bedrock/anthropic.claude-3-7-sonnet-20250219-v1:0
```

**Code changes**: Edit `DEFAULT_MODEL_ASSIGNMENTS` in `src/hotel_revenue_optimization/utils/model_config.py`

### Extending Input Processing

**Add keyword categories** in `main.py`:
- `hotel_keywords`: Terms indicating hotel-related queries
- `irrelevant_keywords`: Terms for non-hotel queries (politics, weather, etc.)
- `booking_keywords`: Terms indicating booking requests

**Add error response types** in `main.py`:
- Define new error type (e.g., "insufficient_context")
- Return structured JSON with `error`, `message`, `suggestion` fields

**Update NLP defaults** in `nlp_processor.py`:
- Modify `defaults` dictionary for new extractable fields
- Update `process_input()` logic for new extraction patterns

### Testing Workflow

```bash
# 1. Local testing
python -m src.hotel_revenue_optimization.main       # Run with defaults
python test_complete_system.py                      # Structured input test
python test_natural_language.py                     # NLP test
python test_error_handling.py                       # Error handling test

# 2. Local AgentCore testing
agentcore launch --local
agentcore invoke --local '{"prompt": "..."}'

# 3. AWS deployment
agentcore launch
agentcore invoke '{"prompt": "..."}'

# 4. Docker testing
docker build -t bedrock_agentcore-hotel_revenue_optimization .
docker run -d -p 8080:8080 --name test-hotel [env vars] bedrock_agentcore-hotel_revenue_optimization:latest
curl -X POST http://localhost:8080/invocations -H "Content-Type: application/json" -d '{"prompt": "..."}'
```

## Key Files Reference

**Core Execution**:
- `src/hotel_revenue_optimization/main.py:23` - `@app.entrypoint` decorated `run()` function
- `src/hotel_revenue_optimization/crew.py:27` - `HotelRevenueOptimizationCrew` class definition
- `src/hotel_revenue_optimization/crew.py:90-156` - Agent creation methods (market_analyst, demand_forecaster, pricing_strategist, revenue_manager)

**Configuration**:
- `src/hotel_revenue_optimization/utils/model_config.py:9-46` - Model tier definitions (AMAZON_TIERS, ANTHROPIC_TIERS, HYBRID_TIERS)
- `src/hotel_revenue_optimization/utils/model_config.py:49-54` - Agent tier assignments
- `src/hotel_revenue_optimization/config/agents.yaml` - Agent role/goal/backstory definitions
- `src/hotel_revenue_optimization/config/tasks_optimized.yaml` - Task descriptions with placeholders

**Input Processing**:
- `src/hotel_revenue_optimization/main.py:62-87` - Multi-format input handling (prompt/message/JSON)
- `src/hotel_revenue_optimization/utils/nlp_processor.py` - Natural language extraction logic

**Utilities**:
- `src/hotel_revenue_optimization/utils/observability.py` - Event logging system
- `src/hotel_revenue_optimization/utils/model_wrapper.py` - Bedrock API wrapper with retries
- `src/hotel_revenue_optimization/utils/nova_llm.py` - Amazon Nova LLM instance creation
- `src/hotel_revenue_optimization/utils/markdown_formatter.py` - Report formatting

## Important Requirements

**AWS Setup**:
- AWS credentials configured with Bedrock access (Claude and Nova models)
- Default region: `us-east-1` (override with `AWS_REGION` environment variable)
- Required role: `BedrockAgentCoreRole` with appropriate permissions
- Model access: Ensure account has access to models in active provider tier

**Environment**:
- Python: >=3.10, <3.14
- Docker: Required for containerized deployment
- Output directory: System creates `output/` if not exists
- Dependencies: gcc and python3-dev required for psutil (configured in Dockerfile)

**Performance Notes**:
- HYBRID provider: ~46s execution (fastest, balanced quality)
- ANTHROPIC provider: ~51s execution (highest quality)
- AMAZON provider: ~52s execution (most cost-effective)
- Planning: Crew uses tier1 model for task planning with Titan embeddings
