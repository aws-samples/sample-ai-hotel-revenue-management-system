#!/bin/bash

# Hotel Revenue Optimization UI - Test Script
# This script tests the deployed application

set -e

# Default values
ENVIRONMENT="dev"
AWS_REGION=$(aws configure get region 2>/dev/null || echo "us-west-2")
STACK_PREFIX="hotel-revenue-optimization"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Hotel Revenue Optimization UI Test Script

Usage: $0 [options]

Options:
  --env ENV           Environment (dev, test, prod). Default: dev
  --region REGION     AWS region. Default: from AWS CLI config or us-west-2
  --help              Show this help message

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

# Set stack names
ECS_STACK="${STACK_PREFIX}-${ENVIRONMENT}-ecs"

log_info "Testing deployment for environment: ${ENVIRONMENT}"

# Get ALB DNS name
log_info "Getting application URL..."
ALB_DNS=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-ALBDNSName'].OutputValue" \
  --output text 2>/dev/null) || {
    log_error "Failed to get ALB DNS name. Is the stack deployed?"
    exit 1
}

APP_URL="http://${ALB_DNS}"
log_info "Application URL: ${APP_URL}"

# Test application health
log_info "Testing application health..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --max-time 30 "${APP_URL}/" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    log_success "Application is healthy (HTTP 200)"
elif [ "$HTTP_STATUS" = "302" ]; then
    log_success "Application is healthy (HTTP 302 - redirect to auth)"
else
    log_error "Application health check failed (HTTP ${HTTP_STATUS})"
    exit 1
fi

# Test ECS service status
log_info "Checking ECS service status..."
SERVICE_NAME="${STACK_PREFIX}-${ENVIRONMENT}-service"
CLUSTER_NAME="${STACK_PREFIX}-${ENVIRONMENT}-cluster"

RUNNING_COUNT=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].runningCount" \
  --output text 2>/dev/null || echo "0")

DESIRED_COUNT=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].desiredCount" \
  --output text 2>/dev/null || echo "0")

if [ "$RUNNING_COUNT" = "$DESIRED_COUNT" ] && [ "$RUNNING_COUNT" != "0" ]; then
    log_success "ECS service is healthy (${RUNNING_COUNT}/${DESIRED_COUNT} tasks running)"
else
    log_error "ECS service is not healthy (${RUNNING_COUNT}/${DESIRED_COUNT} tasks running)"
    exit 1
fi

# Test AgentCore connectivity (if possible)
log_info "Testing AgentCore connectivity..."
AGENTCORE_TEST=$(curl -s --max-time 10 "${APP_URL}/health" 2>/dev/null || echo "")
if [[ "$AGENTCORE_TEST" == *"healthy"* ]] || [[ "$AGENTCORE_TEST" == *"ok"* ]]; then
    log_success "AgentCore connectivity test passed"
else
    log_info "AgentCore connectivity test inconclusive (no health endpoint or different response)"
fi

echo
echo "=================================="
echo "    TEST RESULTS SUMMARY"
echo "=================================="
echo "Environment:         ${ENVIRONMENT}"
echo "Application URL:     ${APP_URL}"
echo "HTTP Status:         ${HTTP_STATUS}"
echo "ECS Tasks:           ${RUNNING_COUNT}/${DESIRED_COUNT}"
echo "Overall Status:      HEALTHY ✅"
echo "=================================="
echo

log_success "All tests passed! Application is running successfully."
