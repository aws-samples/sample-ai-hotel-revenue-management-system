# Getting Started with Hotel Revenue Optimization UI

This guide will help you set up and run the Hotel Revenue Optimization UI locally for development purposes.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.10 or higher
- pip (Python package manager)
- Docker (optional, for containerized development)
- AWS CLI, configured with appropriate credentials
- An AWS account with access to:
  - Amazon Cognito
  - Amazon Bedrock with Agents enabled
  - Amazon ECR (for container deployment)

## Local Development Setup

### 1. Clone the Repository

If you haven't already, clone the repository to your local machine:

```bash
git clone git@ssh.gitlab.aws.dev:agenticai-hackthon-25-rdu11/hotel_revenue_optimization_ui.git
cd hotel_revenue_optimization_ui
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory by copying the example:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_APP=app.py
FLASK_ENV=development

# AWS Configuration
AWS_REGION=us-west-2
AWS_DEFAULT_REGION=us-west-2

# Cognito Configuration
COGNITO_USER_POOL_ID=us-west-2_xxxxxxxx
COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
COGNITO_CLIENT_SECRET=
COGNITO_DOMAIN=your-domain

# AgentCore Configuration
AGENTCORE_RUNTIME_ARN=arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/agent-name-xyz

# OpenTelemetry Configuration
OTEL_SDK_DISABLED=true  # Set to false to enable OpenTelemetry
```

### 5. Run the Application

```bash
# Run in development mode
flask run --debug

# Or run with specific host and port
flask run --debug --host=0.0.0.0 --port=5000
```

The application will be available at http://localhost:5000

## Setting Up Cognito for Authentication

### 1. Create a Cognito User Pool

You can create a Cognito User Pool using the AWS Management Console or by deploying the provided CloudFormation template:

```bash
cd infrastructure/cloudformation
aws cloudformation deploy \
  --template-file cognito.yaml \
  --stack-name hotel-revenue-ui-auth \
  --parameter-overrides \
    AppName=hotel-revenue-optimization \
    Environment=dev \
  --capabilities CAPABILITY_IAM
```

### 2. Get the Cognito Configuration

After creating the User Pool, get the necessary configuration values:

```bash
# Get the User Pool ID
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name hotel-revenue-ui-auth \
  --query "Stacks[0].Outputs[?ExportName=='hotel-revenue-optimization-dev-UserPoolId'].OutputValue" \
  --output text)

# Get the Client ID
CLIENT_ID=$(aws cloudformation describe-stacks \
  --stack-name hotel-revenue-ui-auth \
  --query "Stacks[0].Outputs[?ExportName=='hotel-revenue-optimization-dev-UserPoolClientId'].OutputValue" \
  --output text)

# Get the Domain
DOMAIN=$(aws cloudformation describe-stacks \
  --stack-name hotel-revenue-ui-auth \
  --query "Stacks[0].Outputs[?ExportName=='hotel-revenue-optimization-dev-UserPoolDomain'].OutputValue" \
  --output text)

echo "User Pool ID: $USER_POOL_ID"
echo "Client ID: $CLIENT_ID"
echo "Domain: $DOMAIN"
```

Update your `.env` file with these values.

### 3. Create a Test User

Create a test user in your Cognito User Pool:

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username test@example.com \
  --user-attributes \
    Name=email,Value=test@example.com \
    Name=email_verified,Value=true \
    Name=name,Value="Test User" \
  --temporary-password Temp123!
```

## Connecting to Amazon Bedrock Agents

### 1. Get the Agent Runtime ARN

If you've already deployed the Hotel Revenue Optimization agent to Amazon Bedrock, get the runtime ARN:

```bash
# List available agents
aws bedrock-agent list-agents --query "agentSummaries[?agentName=='hotel-revenue-optimization']"

# Get the agent runtime ARN (replace with your actual agent ID)
AGENT_ID="your-agent-id"
AGENTCORE_RUNTIME_ARN="arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/agent-${AGENT_ID}"

echo "AgentCore Runtime ARN: $AGENTCORE_RUNTIME_ARN"
```

Update your `.env` file with this ARN.

### 2. Test the Connection

You can test the connection to the Bedrock agent using the AWS CLI:

```bash
aws bedrock-agent-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --agent-alias-id TSTALIASID \
  --session-id test-session \
  --input-text "Optimize pricing for a 4-star hotel in Miami during summer season"
```

## Running in a Container

### 1. Build the Docker Image

```bash
cd infrastructure/docker
docker build -t hotel-revenue-optimization-ui -f Dockerfile ../..
```

### 2. Run the Container

```bash
docker run -d -p 8080:8080 \
  --env-file ../../.env \
  --name hotel-revenue-ui \
  hotel-revenue-optimization-ui
```

The application will be available at http://localhost:8080

## Deploying to AWS

For full deployment to AWS, use the provided deployment script:

```bash
cd scripts
./deploy.sh --env dev --region us-west-2
```

This will:
1. Build and push the Docker image to ECR
2. Deploy the Cognito resources
3. Deploy the ECS service with the Application Load Balancer

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Check that your Cognito User Pool ID, Client ID, and Domain are correct
   - Ensure the callback URL in Cognito matches your application URL

2. **Bedrock Agent Connection Errors**:
   - Verify that the AgentCore runtime ARN is correct
   - Check that your AWS credentials have permission to invoke the Bedrock agent
   - Ensure the IAM role has the necessary permissions

3. **OpenTelemetry Issues**:
   - If you're having issues with OpenTelemetry, set `OTEL_SDK_DISABLED=true` in your `.env` file

4. **Docker Build Errors**:
   - Make sure Docker is installed and running
   - Check that you're running the build command from the correct directory

For more detailed troubleshooting, check the application logs:

```bash
# For local Flask application
flask --debug run

# For Docker container
docker logs hotel-revenue-ui

# For ECS deployment
aws logs tail /ecs/hotel-revenue-optimization-dev
```
