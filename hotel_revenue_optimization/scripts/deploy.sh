#!/bin/bash
# Hotel Revenue Optimization System Deployment Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Hotel Revenue Optimization System Deployment${NC}"
echo "========================================"

# Create necessary directories
echo -e "${YELLOW}Creating output directories...${NC}"
mkdir -p output/logs
mkdir -p output/reports

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
uv pip install --upgrade -e .

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}AWS credentials not configured or invalid.${NC}"
    echo "Please run 'aws configure' to set up your credentials."
    exit 1
fi

# Check if we're deploying locally or to AWS
if [ "$1" == "--local" ]; then
    echo -e "${YELLOW}Deploying locally...${NC}"
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
        exit 1
    fi
    
    # Launch locally
    echo -e "${YELLOW}Launching AgentCore locally...${NC}"
    agentcore launch --local
    
    echo -e "${GREEN}Local deployment complete!${NC}"
    echo "The API is available at http://localhost:8080"
    echo "To test, use: curl -X POST http://localhost:8080/invocations -H \"Content-Type: application/json\" -d '{\"hotel_name\": \"Grand Pacific Resort\"}'"
    
elif [ "$1" == "--aws" ]; then
    echo -e "${YELLOW}Deploying to AWS...${NC}"
    
    # Configure AgentCore if not already configured
    if [ ! -f .bedrock_agentcore.yaml ]; then
        echo -e "${YELLOW}Configuring AgentCore...${NC}"
        agentcore configure --entrypoint src/hotel_revenue_optimization/main.py --name hotel_revenue_optimization --execution-role BedrockAgentCoreRole
    fi
    
    # Launch to AWS
    echo -e "${YELLOW}Launching AgentCore to AWS...${NC}"
    agentcore launch
    
    echo -e "${GREEN}AWS deployment complete!${NC}"
    echo "To invoke the agent, use: agentcore invoke '{\"hotel_name\": \"Grand Pacific Resort\"}'"
    
else
    echo -e "${RED}Please specify deployment target: --local or --aws${NC}"
    echo "Usage: ./deploy.sh [--local|--aws]"
    exit 1
fi

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "To analyze logs after running the system, use:"
echo "python -m src.hotel_revenue_optimization.utils.analyze_logs output/logs/performance_<timestamp>.json"
