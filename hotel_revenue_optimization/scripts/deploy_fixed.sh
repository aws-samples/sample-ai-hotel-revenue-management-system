#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting deployment with serialization fixes...${NC}"

# Set AWS profile if provided
if [ -n "$1" ]; then
  export AWS_PROFILE=$1
  echo -e "${GREEN}Using AWS profile: ${AWS_PROFILE}${NC}"
else
  echo -e "${YELLOW}No AWS profile specified, using default${NC}"
  export AWS_PROFILE=default
fi

# Set AWS region
export AWS_REGION=us-west-2
export AWS_DEFAULT_REGION=us-west-2

# Disable OpenTelemetry
export OTEL_SDK_DISABLED=true
export OTEL_PYTHON_DISABLED=true
export OTEL_TRACES_EXPORTER=none
export OTEL_METRICS_EXPORTER=none
export OTEL_LOGS_EXPORTER=none

echo -e "${GREEN}Configuring AgentCore...${NC}"
agentcore configure --entrypoint src/hotel_revenue_optimization/main.py --name hotel_revenue_optimization --execution-role BedrockAgentCoreRole

echo -e "${GREEN}Running tests to verify serialization...${NC}"
python fix_serialization.py

echo -e "${GREEN}Launching to AWS...${NC}"
agentcore launch

echo -e "${GREEN}Deployment complete!${NC}"
echo -e "${YELLOW}To invoke the agent, run:${NC}"
echo -e "agentcore invoke '{\"hotel_name\": \"Grand Pacific Resort\", \"hotel_location\": \"Miami, FL\"}'"
