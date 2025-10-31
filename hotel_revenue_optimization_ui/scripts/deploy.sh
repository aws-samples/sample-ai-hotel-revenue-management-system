#!/bin/bash

# Hotel Revenue Optimization UI - Single Deployment Script
# This script handles the complete deployment of the application to AWS

set -e

# Default values
ENVIRONMENT="dev"
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-west-2")
STACK_PREFIX="hotel-revenue-optimization"
SKIP_BUILD=false
FORCE_DEPLOY=false
AGENTCORE_RUNTIME_ARN=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Hotel Revenue Optimization UI Deployment Script

Usage: $0 [options]

Options:
  --env ENV                   Environment (dev, test, prod). Default: dev
  --region REGION             AWS region. Default: from AWS CLI config or us-west-2
  --agentcore-arn ARN         AgentCore runtime ARN. If not provided, will try to read from .env
  --skip-build                Skip Docker image build and push
  --force                     Skip confirmation prompts
  --help                      Show this help message

Examples:
  $0                                                    # Deploy to dev environment
  $0 --env prod --region us-east-1                     # Deploy to prod in us-east-1
  $0 --skip-build --force                              # Quick redeploy without rebuilding
  $0 --agentcore-arn arn:aws:bedrock-agentcore:...     # Specify AgentCore ARN

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --env)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --agentcore-arn)
      AGENTCORE_RUNTIME_ARN="$2"
      shift 2
      ;;
    --skip-build)
      SKIP_BUILD=true
      shift
      ;;
    --force)
      FORCE_DEPLOY=true
      shift
      ;;
    --help)
      show_help
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      show_help
      exit 1
      ;;
  esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, test, or prod."
    exit 1
fi

# Set stack names
COGNITO_STACK="${STACK_PREFIX}-${ENVIRONMENT}-cognito"
COGNITO_SECRET_STACK="${STACK_PREFIX}-${ENVIRONMENT}-cognito-secret"
DYNAMODB_STACK="${STACK_PREFIX}-${ENVIRONMENT}-dynamodb"
SNS_STACK="${STACK_PREFIX}-${ENVIRONMENT}-sns"
ECS_STACK="${STACK_PREFIX}-${ENVIRONMENT}-ecs"

# Get AWS account ID and validate AWS access
log_info "Validating AWS access..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
    log_error "Failed to get AWS account ID. Please check your AWS credentials."
    exit 1
}

# ECR repository URI
ECR_REPO="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${STACK_PREFIX}-ui"

# Get AgentCore runtime ARN if not provided
if [ -z "$AGENTCORE_RUNTIME_ARN" ]; then
    log_info "AgentCore ARN not provided, checking .env file..."
    if [ -f ".env" ]; then
        AGENTCORE_RUNTIME_ARN=$(grep "AGENTCORE_RUNTIME_ARN=" .env | cut -d'=' -f2 | tr -d '"' | tr -d "'")
    fi
fi

if [ -z "$AGENTCORE_RUNTIME_ARN" ]; then
    log_error "AgentCore runtime ARN is required but not provided."
    log_error "Please provide it using --agentcore-arn or set AGENTCORE_RUNTIME_ARN in .env file."
    log_error "Example ARN: arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/agent-name-xyz"
    exit 1
fi

# Display configuration
echo
echo "=================================="
echo "  DEPLOYMENT CONFIGURATION"
echo "=================================="
echo "Environment:      ${ENVIRONMENT}"
echo "AWS Region:       ${AWS_REGION}"
echo "AWS Account:      ${AWS_ACCOUNT_ID}"
echo "Cognito Stack:    ${COGNITO_STACK}"
echo "Secret Stack:     ${COGNITO_SECRET_STACK}"
echo "DynamoDB Stack:   ${DYNAMODB_STACK}"
echo "SNS Stack:        ${SNS_STACK}"
echo "ECS Stack:        ${ECS_STACK}"
echo "ECR Repository:   ${ECR_REPO}"
echo "AgentCore ARN:    ${AGENTCORE_RUNTIME_ARN}"
echo "Skip Build:       ${SKIP_BUILD}"
echo "=================================="
echo

# Confirm deployment
if [[ "$FORCE_DEPLOY" != "true" ]]; then
    read -p "Do you want to proceed with deployment? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "Deployment cancelled."
        exit 0
    fi
fi

# Change to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Build and push Docker image
if [[ "$SKIP_BUILD" != "true" ]]; then
    log_info "Building and pushing Docker image..."
    cd infrastructure/docker
    
    # Set environment variables for the build script
    export AWS_REGION
    export IMAGE_TAG="v$(date +%Y%m%d-%H%M%S)"
    
    ./build_and_push.sh || {
        log_error "Docker build and push failed"
        exit 1
    }
    
    cd ../..
    log_success "Docker image built and pushed successfully"
else
    log_warning "Skipping Docker build (--skip-build flag used)"
    # Get the most recent image tag from ECR
    IMAGE_TAG=$(aws ecr describe-images \
        --repository-name ${STACK_PREFIX}-ui \
        --region ${AWS_REGION} \
        --query 'sort_by(imageDetails,& imagePushedAt)[-1].imageTags[0]' \
        --output text 2>/dev/null || echo "latest")
    log_info "Using existing image tag: ${IMAGE_TAG}"
fi

# Deploy Cognito stack (initial deployment without CloudFront domain)
log_info "Deploying Cognito authentication stack (initial)..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/cognito.yaml \
  --stack-name ${COGNITO_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
  --capabilities CAPABILITY_IAM \
  --region ${AWS_REGION} || {
    log_error "Cognito stack deployment failed"
    exit 1
}
log_success "Cognito stack deployed successfully"

# Deploy DynamoDB stack
log_info "Deploying DynamoDB stack..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/dynamodb.yaml \
  --stack-name ${DYNAMODB_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
  --region ${AWS_REGION} || {
    log_error "DynamoDB stack deployment failed"
    exit 1
}
log_success "DynamoDB stack deployed successfully"

# Deploy SNS stack
log_info "Deploying SNS stack..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/sns.yaml \
  --stack-name ${SNS_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
  --region ${AWS_REGION} || {
    log_error "SNS stack deployment failed"
    exit 1
}
log_success "SNS stack deployed successfully"

# Get Cognito outputs
log_info "Retrieving Cognito configuration..."
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name ${COGNITO_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-UserPoolId'].OutputValue" \
  --output text)

CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name ${COGNITO_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-UserPoolClientId'].OutputValue" \
  --output text)

DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name ${COGNITO_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-UserPoolDomain'].OutputValue" \
  --output text)

# Get client secret
log_info "Retrieving Cognito client secret..."
CLIENT_SECRET=$(aws cognito-idp describe-user-pool-client \
  --user-pool-id ${USER_POOL_ID} \
  --client-id ${CLIENT_ID} \
  --region ${AWS_REGION} \
  --query "UserPoolClient.ClientSecret" \
  --output text)

# Deploy Cognito client secret stack
log_info "Deploying Cognito client secret stack..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/cognito-client-secret.yaml \
  --stack-name ${COGNITO_SECRET_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
    CognitoUserPoolId=${USER_POOL_ID} \
    CognitoClientId=${CLIENT_ID} \
    CognitoClientSecret=${CLIENT_SECRET} \
  --region ${AWS_REGION} || {
    log_error "Cognito secret stack deployment failed"
    exit 1
}
log_success "Cognito secret stack deployed successfully"

log_success "Using AgentCore runtime ARN: ${AGENTCORE_RUNTIME_ARN}"

# Deploy ECS stack
log_info "Deploying ECS application stack (with 20-minute timeout)..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/ecs.yaml \
  --stack-name ${ECS_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
    ImageRepository=${ECR_REPO} \
    ImageTag=${IMAGE_TAG} \
    ContainerPort=8080 \
    DesiredCount=2 \
    CognitoUserPoolId=${USER_POOL_ID} \
    CognitoClientId=${CLIENT_ID} \
    CognitoDomain=${DOMAIN} \
    AgentCoreEndpoint=${AGENTCORE_RUNTIME_ARN} \
  --capabilities CAPABILITY_IAM \
  --region ${AWS_REGION} || {
    log_error "ECS stack deployment failed"
    log_info "Checking stack events for details..."
    aws cloudformation describe-stack-events \
      --stack-name ${ECS_STACK} \
      --region ${AWS_REGION} \
      --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
      --output table
    exit 1
}
log_success "ECS stack deployed successfully"

# Get CloudFront domain name
log_info "Retrieving CloudFront domain..."
CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-CloudFrontDomain'].OutputValue" \
  --output text)

# Update Cognito stack with CloudFront domain
log_info "Updating Cognito stack with CloudFront domain..."
aws cloudformation deploy \
  --template-file infrastructure/cloudformation/cognito.yaml \
  --stack-name ${COGNITO_STACK} \
  --parameter-overrides \
    AppName=${STACK_PREFIX} \
    Environment=${ENVIRONMENT} \
    CloudFrontDomain=${CLOUDFRONT_DOMAIN} \
  --capabilities CAPABILITY_IAM \
  --region ${AWS_REGION} || {
    log_error "Cognito stack update failed"
    exit 1
}
log_success "Cognito stack updated with CloudFront domain"

# Get ALB DNS name
log_info "Retrieving application URL..."
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-ALBDNSName'].OutputValue" \
  --output text)

APPLICATION_URL=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-ApplicationURL'].OutputValue" \
  --output text)

# Final output
echo
echo "=================================="
echo "    DEPLOYMENT SUCCESSFUL! 🎉"
echo "==================================="
echo "DEPLOYMENT COMPLETED SUCCESSFULLY!"
echo "==================================="
echo "Environment:         ${ENVIRONMENT}"
echo "Region:              ${AWS_REGION}"
echo "Application URL:     ${APPLICATION_URL}"
echo "CloudFront Domain:   ${CLOUDFRONT_DOMAIN}"
echo "ALB DNS (internal):  ${ALB_DNS}"
echo "User Pool ID:        ${USER_POOL_ID}"
echo "Client ID:           ${CLIENT_ID}"
echo "Cognito Domain:      ${DOMAIN}"
echo "AgentCore ARN:       ${AGENTCORE_RUNTIME_ARN}"
echo "==================================="
echo
log_success "Deployment completed successfully!"
log_info "You can now access your application at: ${APPLICATION_URL}"
echo
log_info "To validate AgentCore permissions are working correctly, run:"
log_info "./scripts/validate-agentcore.sh --env ${ENVIRONMENT} --region ${AWS_REGION}"
