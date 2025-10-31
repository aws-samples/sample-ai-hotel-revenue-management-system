#!/bin/bash

# =============================================================================
# Hotel Revenue Optimization System - Enhanced Deployment Script
# =============================================================================

set -e

# Default values
REGION="us-east-1"
PROFILE="default"
EXECUTION_ROLE="BedrockAgentCoreRole"
RUNTIME_NAME="hotel_revenue_optimization"
ENTRYPOINT="src/hotel_revenue_optimization/main.py"
DEPLOYMENT_MODE="aws"
FORCE_REBUILD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --execution-role)
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
        --aws)
            DEPLOYMENT_MODE="aws"
            shift
            ;;
        --local)
            DEPLOYMENT_MODE="local"
            shift
            ;;
        --force-rebuild)
            FORCE_REBUILD=true
            shift
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

echo "=== Hotel Revenue Optimization System Deployment ==="
echo "Region: $REGION"
echo "AWS Profile: $PROFILE"
echo "Execution Role: $EXECUTION_ROLE"
echo "Runtime Name: $RUNTIME_NAME"
echo "Entrypoint: $ENTRYPOINT"
echo "Deployment Mode: $DEPLOYMENT_MODE"
echo "Force Rebuild: $FORCE_REBUILD"
echo "=================================================="

# Activate virtual environment
echo "Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade AgentCore SDK to latest version
echo "Upgrading AgentCore SDK to latest version..."
pip install --upgrade bedrock-agentcore bedrock-agentcore-starter-toolkit || {
    echo "Warning: Could not upgrade bedrock-agentcore packages (may not be available)"
    echo "Installing agentcore..."
    pip install --upgrade agentcore
}

# Use existing AgentCore configuration or create new one
if [ -f ".bedrock_agentcore.yaml" ] && [ "$FORCE_REBUILD" = false ]; then
    echo "Using existing AgentCore configuration..."
else
    echo "Configuring AgentCore from scratch..."
    
    # Backup existing files
    if [ -f ".bedrock_agentcore.yaml" ]; then
        echo "Backing up existing .bedrock_agentcore.yaml..."
        mkdir -p backup/$(date +%Y%m%d_%H%M%S)
        cp .bedrock_agentcore.yaml backup/$(date +%Y%m%d_%H%M%S)/
    fi
    
    if [ -f "Dockerfile" ]; then
        echo "Backing up existing Dockerfile..."
        mkdir -p backup/$(date +%Y%m%d_%H%M%S)
        cp Dockerfile backup/$(date +%Y%m%d_%H%M%S)/
    fi
    
    if [ -f ".dockerignore" ]; then
        echo "Backing up existing .dockerignore..."
        mkdir -p backup/$(date +%Y%m%d_%H%M%S)
        cp .dockerignore backup/$(date +%Y%m%d_%H%M%S)/
    fi
    
    # Configure AgentCore
    echo "Configuring AgentCore..."
    agentcore configure \
        --entrypoint "$ENTRYPOINT" \
        --name "$RUNTIME_NAME" \
        --execution-role "$EXECUTION_ROLE" \
        --region "$REGION"
fi

# Check and fix Dockerfile for build dependencies
echo "Checking and fixing Dockerfile..."
if [ -f "Dockerfile" ]; then
    # Check if Dockerfile has build dependencies
    if ! grep -q "gcc python3-dev" Dockerfile; then
        echo "Fixing Dockerfile - adding build dependencies for psutil..."
        
        # Create a fixed Dockerfile
        cat > Dockerfile << 'EOF'
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim
WORKDIR /app

# Configure UV for container environment
ENV UV_SYSTEM_PYTHON=1 UV_COMPILE_BYTECODE=1

# Install build dependencies for psutil and other native packages
RUN apt-get update && \
    apt-get install -y gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

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
        
        echo "✅ Dockerfile fixed with build dependencies"
    else
        echo "✅ Dockerfile already has build dependencies"
    fi
else
    echo "❌ No Dockerfile found - AgentCore configure may have failed"
    exit 1
fi

# Update .dockerignore to include important files
echo "Updating .dockerignore to include Dockerfile and config..."
cat > .dockerignore << 'EOF'
# Version control
.git
.gitignore

# Python
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# IDE
.vscode
.idea
*.swp
*.swo

# Project specific
venv/
.env
*.log
backup/
output/
logs/

# Keep these files in the container
!Dockerfile
!.dockerignore
!.bedrock_agentcore.yaml
EOF

# Ensure output directory exists
echo "Ensuring output directory exists..."
mkdir -p output

echo ""
echo "✅ Build configuration completed successfully!"
echo "📁 Backup files saved in: backup/$(date +%Y%m%d_%H%M%S)"
echo "🔧 Configuration files created/updated"
echo "🐳 Dockerfile fixed for build dependencies"
echo ""

if [ "$DEPLOYMENT_MODE" = "aws" ]; then
    echo "🚀 Next step: Deploy using:"
    echo "   agentcore launch"
elif [ "$DEPLOYMENT_MODE" = "local" ]; then
    echo "🚀 Next step: Deploy using:"
    echo "   agentcore launch --local"
fi
