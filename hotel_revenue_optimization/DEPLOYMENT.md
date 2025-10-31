# Hotel Revenue Optimization System - Deployment Guide

This guide covers the deployment of the Hotel Revenue Optimization System to AWS Bedrock AgentCore with multiple deployment approaches.

## Prerequisites

* Python >=3.10 <3.14
* AWS CLI configured with appropriate permissions
* Amazon Bedrock access with Claude models enabled
* AgentCore CLI installed

## Deployment Approaches

### 1. Quick Deployment (Recommended for Teams)

**Use this when**: Working with committed configuration files and want consistent deployments across team members.

```bash
# Uses existing .bedrock_agentcore.yaml and Dockerfile
./deploy.sh --region us-east-1 --aws
```

**Benefits**:
- Fast deployment using committed configuration
- Consistent across team members
- No need to reconfigure

### 2. Build from Scratch

**Use this when**: Need to create fresh configuration or fix build issues.

```bash
# Creates new configuration and fixes Dockerfile issues
./build.sh --region us-east-1 --aws
```

**What it does**:
- Backs up existing config files with timestamp
- Creates fresh `.bedrock_agentcore.yaml` configuration
- Auto-detects and fixes Dockerfile build dependencies
- Deploys with corrected configuration

### 3. Manual AgentCore Commands

**Use this when**: Need fine-grained control over the deployment process.

#### Option A: Default (CodeBuild + Cloud Runtime) - RECOMMENDED
```bash
# No Docker required locally - builds in cloud
agentcore launch
```

#### Option B: Local Development
```bash
# Requires Docker/Finch/Podman locally
agentcore launch --local
```

#### Option C: Hybrid (Local Build + Cloud Runtime)
```bash
# Build locally, deploy to cloud - requires Docker
agentcore launch --local-build
```

## AgentCore Configuration Management

### Committed Configuration Files

The repository now includes:
- `.bedrock_agentcore.yaml` - Agent configuration (name, execution role, ECR repo)
- `Dockerfile` - Fixed container configuration with build dependencies

### When Configuration is Auto-Generated

If no configuration exists, AgentCore automatically:
- Detects Python version (e.g., 3.13)
- Selects optimized base image (`ghcr.io/astral-sh/uv:python3.13-bookworm-slim`)
- Creates ARM64 container for AWS deployment
- May need manual fixes for build dependencies

## Deployment Scripts

### deploy.sh - Quick Team Deployment
```bash
# Deploy to AWS us-east-1
./deploy.sh --region us-east-1 --aws

# Deploy locally (requires Docker)
./deploy.sh --local

# Custom configuration
./deploy.sh --region eu-west-1 --role MyCustomRole --name my-hotel-app
```

### build.sh - Fresh Configuration
```bash
# Build and deploy to AWS us-east-1
./build.sh --region us-east-1 --aws

# Build and deploy locally  
./build.sh --local

# Custom configuration with fresh build
./build.sh --region eu-west-1 --role MyCustomRole --name my-hotel-app
```

## Common Build Issues and Solutions

### Issue: psutil Build Failure
**Error**: `gcc: command not found` during Docker build

**Solution**: The `build.sh` script automatically detects and fixes this by adding:
```dockerfile
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
```

### Issue: Missing Configuration
**Error**: No `.bedrock_agentcore.yaml` found

**Solution**: Use `build.sh` to create fresh configuration or run:
```bash
agentcore configure \
  --entrypoint src/hotel_revenue_optimization/main.py \
  --name hotel_revenue_optimization \
  --execution-role BedrockAgentCoreRole \
  --region us-east-1
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
MODEL_MARKET_ANALYST=bedrock/anthropic.claude-3-haiku-20240307-v1:0
MODEL_DEMAND_FORECASTER=bedrock/anthropic.claude-3-haiku-20240307-v1:0
MODEL_PRICING_STRATEGIST=bedrock/anthropic.claude-3-sonnet-20240229-v1:0
MODEL_REVENUE_MANAGER=bedrock/anthropic.claude-3-haiku-20240307-v1:0
AWS_REGION=us-east-1
```

## Testing the Deployment

After deployment, test the agent:

```bash
agentcore invoke '{"prompt": "Analyze revenue for The Ritz-Carlton in San Francisco. Current ADR $450, occupancy 68%."}'
```

## Monitoring

Monitor the deployed agent using CloudWatch logs:

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/hotel_revenue_optimization-<id>-DEFAULT --follow
```

## Team Workflow Recommendations

### For New Team Members
1. Clone repository (includes committed config files)
2. Run `./deploy.sh --region us-east-1 --aws`
3. Test with `agentcore invoke`

### For Configuration Changes
1. Use `./build.sh` to create fresh configuration
2. Test deployment
3. Commit updated config files for team

### For Development
1. Use `agentcore launch --local` for rapid iteration
2. Use `./deploy.sh --aws` for cloud testing
3. Use `./build.sh` when configuration needs updates
