#!/bin/bash

# Hotel Revenue Optimization UI - AgentCore Validation Script
# This script validates that AgentCore permissions are properly configured

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
Hotel Revenue Optimization UI - AgentCore Validation Script

Usage: $0 [options]

Options:
  --env ENV                   Environment (dev, test, prod). Default: dev
  --region REGION             AWS region. Default: from AWS CLI config or us-west-2
  --help                      Show this help message

Examples:
  $0                          # Validate dev environment
  $0 --env prod --region us-east-1    # Validate prod in us-east-1

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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|test|prod)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT. Must be dev, test, or prod."
    exit 1
fi

# Set stack names
ECS_STACK="${STACK_PREFIX}-${ENVIRONMENT}-ecs"

echo
echo "=================================="
echo "  AGENTCORE VALIDATION"
echo "=================================="
echo "Environment:      ${ENVIRONMENT}"
echo "AWS Region:       ${AWS_REGION}"
echo "ECS Stack:        ${ECS_STACK}"
echo "=================================="
echo

# Check if ECS stack exists
log_info "Checking if ECS stack exists..."
if ! aws cloudformation describe-stacks --stack-name ${ECS_STACK} --region ${AWS_REGION} >/dev/null 2>&1; then
    log_error "ECS stack '${ECS_STACK}' not found. Please deploy the application first."
    exit 1
fi
log_success "ECS stack found"

# Get ECS cluster and service names
log_info "Retrieving ECS configuration..."
CLUSTER_NAME=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-ECSClusterName'].OutputValue" \
  --output text)

SERVICE_NAME=$(aws cloudformation describe-stacks \
  --stack-name ${ECS_STACK} \
  --region ${AWS_REGION} \
  --query "Stacks[0].Outputs[?ExportName=='${STACK_PREFIX}-${ENVIRONMENT}-ECSServiceName'].OutputValue" \
  --output text)

log_info "Cluster: ${CLUSTER_NAME}"
log_info "Service: ${SERVICE_NAME}"

# Check ECS service status
log_info "Checking ECS service status..."
SERVICE_STATUS=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].status" \
  --output text)

RUNNING_COUNT=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].runningCount" \
  --output text)

DESIRED_COUNT=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].desiredCount" \
  --output text)

if [[ "$SERVICE_STATUS" != "ACTIVE" ]]; then
    log_error "ECS service is not active. Status: ${SERVICE_STATUS}"
    exit 1
fi

if [[ "$RUNNING_COUNT" != "$DESIRED_COUNT" ]]; then
    log_warning "ECS service not at desired capacity. Running: ${RUNNING_COUNT}, Desired: ${DESIRED_COUNT}"
else
    log_success "ECS service is healthy (${RUNNING_COUNT}/${DESIRED_COUNT} tasks running)"
fi

# Get task definition ARN
TASK_DEFINITION_ARN=$(aws ecs describe-services \
  --cluster ${CLUSTER_NAME} \
  --services ${SERVICE_NAME} \
  --region ${AWS_REGION} \
  --query "services[0].taskDefinition" \
  --output text)

log_info "Task Definition: ${TASK_DEFINITION_ARN}"

# Check task role permissions
log_info "Validating task role permissions..."
TASK_ROLE_ARN=$(aws ecs describe-task-definition \
  --task-definition ${TASK_DEFINITION_ARN} \
  --region ${AWS_REGION} \
  --query "taskDefinition.taskRoleArn" \
  --output text)

if [[ "$TASK_ROLE_ARN" == "null" || -z "$TASK_ROLE_ARN" ]]; then
    log_error "No task role found in task definition"
    exit 1
fi

ROLE_NAME=$(echo ${TASK_ROLE_ARN} | cut -d'/' -f2)
log_info "Task Role: ${ROLE_NAME}"

# Check if role has required policies
log_info "Checking attached policies..."
ATTACHED_POLICIES=$(aws iam list-attached-role-policies \
  --role-name ${ROLE_NAME} \
  --region ${AWS_REGION} \
  --query "AttachedPolicies[].PolicyName" \
  --output text)

echo "Attached policies: ${ATTACHED_POLICIES}"

# Check for AgentCore permissions in inline policies
INLINE_POLICIES=$(aws iam list-role-policies \
  --role-name ${ROLE_NAME} \
  --region ${AWS_REGION} \
  --query "PolicyNames" \
  --output text)

AGENTCORE_PERMISSION_FOUND=false

if [[ "$INLINE_POLICIES" == *"AgentCoreInvokePolicy"* ]]; then
    log_info "Found AgentCoreInvokePolicy inline policy"
    
    # Check the policy content
    POLICY_DOCUMENT=$(aws iam get-role-policy \
      --role-name ${ROLE_NAME} \
      --policy-name AgentCoreInvokePolicy \
      --region ${AWS_REGION} \
      --query "PolicyDocument" \
      --output json)
    
    if [[ "$POLICY_DOCUMENT" == *"bedrock-agentcore:InvokeAgentRuntime"* ]]; then
        log_success "AgentCore InvokeAgentRuntime permission found"
        AGENTCORE_PERMISSION_FOUND=true
    fi
fi

if [[ "$AGENTCORE_PERMISSION_FOUND" != "true" ]]; then
    log_error "AgentCore permissions not found in task role"
    log_error "The task role should have a policy with 'bedrock-agentcore:InvokeAgentRuntime' permission"
    exit 1
fi

# Get AgentCore ARN from task definition
log_info "Checking AgentCore configuration..."
AGENTCORE_ARN=$(aws ecs describe-task-definition \
  --task-definition ${TASK_DEFINITION_ARN} \
  --region ${AWS_REGION} \
  --query "taskDefinition.containerDefinitions[0].environment[?name=='AGENTCORE_RUNTIME_ARN'].value" \
  --output text)

if [[ -z "$AGENTCORE_ARN" || "$AGENTCORE_ARN" == "null" ]]; then
    log_error "AGENTCORE_RUNTIME_ARN environment variable not found in task definition"
    exit 1
fi

log_success "AgentCore ARN configured: ${AGENTCORE_ARN}"

# Check recent application logs for AgentCore errors
log_info "Checking recent application logs for AgentCore errors..."
LOG_GROUP="/ecs/${STACK_PREFIX}-${ENVIRONMENT}"

# Get recent log streams
RECENT_STREAMS=$(aws logs describe-log-streams \
  --log-group-name ${LOG_GROUP} \
  --order-by LastEventTime \
  --descending \
  --max-items 3 \
  --region ${AWS_REGION} \
  --query "logStreams[].logStreamName" \
  --output text 2>/dev/null || echo "")

if [[ -z "$RECENT_STREAMS" ]]; then
    log_warning "No recent log streams found in ${LOG_GROUP}"
else
    log_info "Checking logs for AgentCore errors..."
    
    ERROR_FOUND=false
    for stream in $RECENT_STREAMS; do
        # Check for AgentCore access denied errors
        ERROR_COUNT=$(aws logs filter-log-events \
          --log-group-name ${LOG_GROUP} \
          --log-stream-names ${stream} \
          --filter-pattern "AccessDeniedException bedrock-agentcore" \
          --region ${AWS_REGION} \
          --query "length(events)" \
          --output text 2>/dev/null || echo "0")
        
        if [[ "$ERROR_COUNT" != "0" ]]; then
            ERROR_FOUND=true
            break
        fi
    done
    
    if [[ "$ERROR_FOUND" == "true" ]]; then
        log_error "Found AgentCore AccessDeniedException errors in recent logs"
        log_error "This indicates the task role permissions are not working correctly"
        exit 1
    else
        log_success "No AgentCore permission errors found in recent logs"
    fi
fi

# Final validation summary
echo
echo "=================================="
echo "    VALIDATION SUCCESSFUL! ✅"
echo "=================================="
echo "✅ ECS stack exists and is active"
echo "✅ ECS service is running (${RUNNING_COUNT}/${DESIRED_COUNT} tasks)"
echo "✅ Task role has AgentCore permissions"
echo "✅ AgentCore ARN is configured"
echo "✅ No recent permission errors in logs"
echo "=================================="
echo

log_success "AgentCore configuration validation completed successfully!"
log_info "Your application should be able to connect to AgentCore without falling back to mock responses."
