#!/bin/bash

# Docker Build and Push Script for Hotel Revenue Optimization UI
# Builds and pushes Docker image to ECR with proper platform support for ECS Fargate

set -e

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

# Get the AWS account ID
log_info "Getting AWS account ID..."
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null) || {
    log_error "Failed to get AWS account ID. Please check your AWS credentials."
    exit 1
}

# Set the region (use environment variable or default)
AWS_REGION=${AWS_REGION:-us-west-2}

# Set the repository name
REPO_NAME=hotel-revenue-optimization-ui

# Set the image tag (use environment variable or default)
IMAGE_TAG=${IMAGE_TAG:-latest}

# Full image name
IMAGE_NAME=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}

log_info "Build configuration:"
echo "  Repository: ${REPO_NAME}"
echo "  Tag: ${IMAGE_TAG}"
echo "  Full image name: ${IMAGE_NAME}"
echo "  Region: ${AWS_REGION}"

# Check if the repository exists, if not create it
log_info "Checking ECR repository..."
aws ecr describe-repositories --repository-names ${REPO_NAME} --region ${AWS_REGION} >/dev/null 2>&1 || {
    log_info "Creating ECR repository..."
    aws ecr create-repository --repository-name ${REPO_NAME} --region ${AWS_REGION} >/dev/null
    log_success "ECR repository created"
}

# Get the login command from ECR and execute it
log_info "Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com || {
    log_error "Failed to login to ECR"
    exit 1
}
log_success "Successfully logged into ECR"

# Build the Docker image with platform specification for ECS Fargate
log_info "Building Docker image for linux/amd64 platform..."
docker buildx build \
    --platform linux/amd64 \
    -t ${REPO_NAME}:${IMAGE_TAG} \
    -f ../../Dockerfile \
    ../.. || {
    log_error "Docker build failed"
    exit 1
}
log_success "Docker image built successfully"

# Tag the image
log_info "Tagging image as ${IMAGE_NAME}..."
docker tag ${REPO_NAME}:${IMAGE_TAG} ${IMAGE_NAME} || {
    log_error "Failed to tag image"
    exit 1
}

# Push the image to ECR
log_info "Pushing image to ECR..."
docker push ${IMAGE_NAME} || {
    log_error "Failed to push image to ECR"
    exit 1
}

log_success "Image pushed successfully to ${IMAGE_NAME}"
echo "Image URI: ${IMAGE_NAME}"
