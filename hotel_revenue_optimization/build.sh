#!/bin/bash

# Hotel Revenue Optimization System - Build Configuration Script
# This script rebuilds AgentCore configuration and Dockerfile from scratch

set -e  # Exit on error

# Default values
REGION="us-east-1"
AWS_PROFILE="default"
EXECUTION_ROLE="BedrockAgentCoreRole"
RUNTIME_NAME="hotel_revenue_optimization"
ENTRYPOINT="src/hotel_revenue_optimization/main.py"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      REGION="$2"
      shift 2
      ;;
    --profile)
      AWS_PROFILE="$2"
      shift 2
      ;;
    --role)
      EXECUTION_ROLE="$2"
      shift 2
      ;;
    --name)
      RUNTIME_NAME="$2"
      shift 2
      ;;
    --entrypoint)
      ENTRYPOINT="$2"
      shift 2
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --region REGION       AWS region (default: us-west-2)"
      echo "  --profile PROFILE     AWS profile (default: default)"
      echo "  --role ROLE           AWS execution role (default: BedrockAgentCoreRole)"
      echo "  --name NAME           Runtime name (default: hotel_revenue_optimization)"
      echo "  --entrypoint FILE     Entrypoint file (default: src/hotel_revenue_optimization/main.py)"
      echo "  --help                Show this help message"
      echo ""
      echo "After building, use deploy.sh to launch:"
      echo "  ./deploy.sh --region $REGION --profile $AWS_PROFILE --aws"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "=== Hotel Revenue Optimization System - Build Configuration ==="
echo "Region: $REGION"
echo "AWS Profile: $AWS_PROFILE"
echo "Execution Role: $EXECUTION_ROLE"
echo "Runtime Name: $RUNTIME_NAME"
echo "Entrypoint: $ENTRYPOINT"
echo "=============================================================="

# Activate virtual environment and install AgentCore SDK
echo "Activating virtual environment..."
source venv/bin/activate

# Set AWS profile
export AWS_PROFILE=$AWS_PROFILE

echo "Installing AgentCore SDK..."
pip install bedrock-agentcore-sdk || pip install amazon-bedrock-agentcore || pip install agentcore || echo "AgentCore SDK not found in PyPI, checking if already installed..."

# Create backup folder with timestamp
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup existing files if they exist
if [ -f ".bedrock_agentcore.yaml" ]; then
  echo "Backing up existing .bedrock_agentcore.yaml..."
  cp .bedrock_agentcore.yaml "$BACKUP_DIR/"
  rm .bedrock_agentcore.yaml
fi

if [ -f "Dockerfile" ]; then
  echo "Backing up existing Dockerfile..."
  cp Dockerfile "$BACKUP_DIR/"
  rm Dockerfile
fi

if [ -f ".dockerignore" ]; then
  echo "Backing up existing .dockerignore..."
  cp .dockerignore "$BACKUP_DIR/"
fi

echo "Backup created in: $BACKUP_DIR"

# Configure AgentCore from scratch
echo "Configuring AgentCore from scratch..."
agentcore configure \
  --entrypoint "$ENTRYPOINT" \
  --name "$RUNTIME_NAME" \
  --execution-role "$EXECUTION_ROLE" \
  --region "$REGION"

# Check and fix Dockerfile if it has build dependency issues
echo "Checking and fixing Dockerfile..."
if [ -f "Dockerfile" ]; then
  # Check if Dockerfile is missing build dependencies for psutil
  if grep -q "psutil" requirements.txt && ! grep -q "gcc" Dockerfile; then
    echo "Fixing Dockerfile - adding build dependencies for psutil..."
    
    # Create a fixed Dockerfile
    cat > Dockerfile.fixed << 'EOF'
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install build dependencies for packages that need compilation
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
# Install from requirements file
RUN uv pip install -r requirements.txt

RUN uv pip install aws-opentelemetry-distro>=0.10.1

# Set AWS region environment variable
ENV AWS_REGION=us-east-1
ENV AWS_DEFAULT_REGION=us-east-1

# Signal that this is running in Docker for host binding logic
ENV DOCKER_CONTAINER=1

# Create non-root user
RUN useradd -m -u 1000 bedrock_agentcore
USER bedrock_agentcore

EXPOSE 8080
EXPOSE 8000

# Copy entire project (respecting .dockerignore)
COPY . .

# Use the full module path
CMD ["opentelemetry-instrument", "python", "-m", "src.hotel_revenue_optimization.main"]
EOF
    
    # Replace the original Dockerfile
    mv Dockerfile.fixed Dockerfile
    echo "✅ Dockerfile fixed with build dependencies"
  else
    echo "✅ Dockerfile looks good"
  fi
else
  echo "❌ No Dockerfile found after configuration"
  exit 1
fi

# Update .dockerignore to not exclude Dockerfile and config
if [ -f ".dockerignore" ]; then
  echo "Updating .dockerignore to include Dockerfile and config..."
  sed -i.bak 's/^Dockerfile$/# Dockerfile - KEEP THIS FOR BUILD/' .dockerignore
  sed -i.bak 's/^\.dockerignore$/# .dockerignore - KEEP THIS FOR BUILD/' .dockerignore
  rm .dockerignore.bak
fi

echo "Ensuring output directory exists..."
mkdir -p output

echo ""
echo "✅ Build configuration completed successfully!"
echo "📁 Backup files saved in: $BACKUP_DIR"
echo "🔧 Configuration files created fresh"
echo "🐳 Dockerfile fixed for build dependencies"
echo ""
echo "🚀 Next step: Deploy using:"
echo "   ./deploy.sh --region $REGION --profile $AWS_PROFILE --aws"
echo "   ./deploy.sh --region $REGION --profile $AWS_PROFILE --local"
