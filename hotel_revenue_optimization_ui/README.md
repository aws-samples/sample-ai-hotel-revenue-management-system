# Hotel Revenue Optimization UI

A modern web-based user interface for the Hotel Revenue Optimization system powered by Amazon Bedrock AgentCore.

## Overview

This application provides an intuitive interface for hotel managers to optimize their revenue using AI-powered recommendations. It connects to an Amazon Bedrock AgentCore agent that analyzes hotel data and provides pricing strategies, demand forecasts, and competitor analysis.

## Features

- **Natural Language Interface**: Ask questions in plain English
- **Structured Forms**: Provide specific hotel information through guided forms
- **Interactive Dashboard**: Quick actions and sample queries
- **Query History**: Track previous recommendations and insights
- **Error Handling**: User-friendly error messages with helpful guidance
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Secure Authentication**: AWS Cognito-based user authentication

## Architecture

The application is built with modern cloud-native architecture:

- **Frontend**: Flask web application with Bootstrap UI
- **Authentication**: Amazon Cognito User Pools
- **AI Engine**: Amazon Bedrock AgentCore
- **Container Platform**: Amazon ECS Fargate
- **Load Balancing**: Application Load Balancer
- **Content Delivery**: Amazon CloudFront
- **Container Registry**: Amazon ECR
- **Monitoring**: Amazon CloudWatch

## Prerequisites

- AWS CLI configured with appropriate permissions
- Docker installed and running
- Python 3.10+ (for local development)
- Access to Amazon Bedrock with Claude models enabled
- Hotel Revenue Optimization agent deployed to Amazon Bedrock AgentCore

## Quick Start

### 1. Clone the Repository

```bash
git clone git@ssh.gitlab.aws.dev:agenticai-hackthon-25-rdu11/hotel_revenue_optimization_ui.git
cd hotel_revenue_optimization_ui
```

### 2. Configure Environment

Create a `.env` file with your configuration:

```bash
cp .env.example .env
# Edit .env with your AgentCore runtime ARN
```

Required environment variables:
- `AGENTCORE_RUNTIME_ARN`: Your AgentCore runtime ARN (e.g., `arn:aws:bedrock-agentcore:us-west-2:123456789012:runtime/agent-name-xyz`)

### 3. Deploy to AWS

```bash
# Deploy to development environment
./scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh --env prod --region us-east-1

# Quick redeploy without rebuilding Docker image
./scripts/deploy.sh --skip-build --force
```

### 4. Test the Deployment

```bash
# Run health checks
./scripts/test.sh

# Test specific environment
./scripts/test.sh --env prod --region us-east-1
```

## Local Development

### Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables in `.env`:
   ```bash
   FLASK_ENV=development
   FLASK_DEBUG=1
   DISABLE_AUTH=True
   AGENTCORE_RUNTIME_ARN=your-runtime-arn
   ```

4. Run the application:
   ```bash
   flask run --debug
   ```

5. Open your browser and navigate to http://localhost:5000

### Testing Without Amazon Bedrock AgentCore

For local testing without connecting to Amazon Bedrock AgentCore, leave the `AGENTCORE_RUNTIME_ARN` empty in the `.env` file. The application will use mock responses for testing.

## Deployment Options

### Single Command Deployment

The `./scripts/deploy.sh` script handles the complete deployment process:

```bash
# Basic deployment
./scripts/deploy.sh

# Advanced options
./scripts/deploy.sh --env prod \
                   --region us-east-1 \
                   --agentcore-arn arn:aws:bedrock-agentcore:... \
                   --force
```

**Available Options:**
- `--env ENV`: Environment (dev, test, prod). Default: dev
- `--region REGION`: AWS region. Default: from AWS CLI config or us-west-2
- `--agentcore-arn ARN`: AgentCore runtime ARN. If not provided, reads from .env
- `--skip-build`: Skip Docker image build and push
- `--force`: Skip confirmation prompts
- `--help`: Show help message

### What the Deployment Script Does

1. **Validates AWS Access**: Ensures proper AWS credentials and permissions
2. **Builds Docker Image**: Creates platform-specific image for ECS Fargate (linux/amd64)
3. **Pushes to ECR**: Uploads image to Amazon Elastic Container Registry
4. **Deploys Cognito**: Sets up user authentication with AWS Cognito
5. **Configures Secrets**: Manages Cognito client secrets securely
6. **Deploys ECS Infrastructure**: Creates VPC, ALB, ECS cluster, and services
7. **Validates Deployment**: Confirms all resources are healthy

### Infrastructure Components

The deployment creates:

- **VPC**: Isolated network with public subnets across multiple AZs
- **Application Load Balancer**: Distributes traffic with CloudFront integration
- **ECS Fargate Cluster**: Serverless container platform
- **Security Groups**: Restricts access to CloudFront traffic only
- **IAM Roles**: Least-privilege access for ECS tasks and Bedrock
- **CloudWatch Logs**: Centralized logging with 30-day retention
- **Cognito User Pool**: User authentication and management

## Testing

### Automated Testing

```bash
# Test deployment health
./scripts/test.sh

# Test specific environment
./scripts/test.sh --env prod --region us-east-1
```

The test script validates:
- Application HTTP response (200 or 302 for auth redirect)
- ECS service health (running tasks match desired count)
- AgentCore connectivity (if health endpoint available)

### Manual Testing

1. **Access the Application**: Navigate to the provided URL after deployment
2. **Authentication**: Sign in through Cognito (if enabled)
3. **Submit Queries**: Test the natural language interface
4. **Check Responses**: Verify AI-powered recommendations
5. **Error Handling**: Test with invalid queries to see user-friendly error messages

## Configuration

### Environment Variables

**Production Environment:**
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`
- `DISABLE_AUTH=False`
- `AGENTCORE_RUNTIME_ARN=<your-runtime-arn>`
- `AWS_REGION=<your-region>`

**Development Environment:**
- `FLASK_ENV=development`
- `FLASK_DEBUG=1`
- `DISABLE_AUTH=True`
- `AGENTCORE_RUNTIME_ARN=<your-runtime-arn>`

### Cognito Configuration

The deployment automatically configures:
- User Pool with email-based authentication
- App Client with OAuth 2.0 flows
- Domain for hosted UI
- Secure client secret management

### Security

- **Network Security**: ALB restricted to CloudFront traffic only
- **Authentication**: AWS Cognito with secure token handling
- **IAM Permissions**: Least-privilege access to AWS services
- **Container Security**: Non-root user, minimal base image
- **Secrets Management**: AWS Secrets Manager for sensitive data

### Amazon Bedrock AgentCore Permissions

The application requires specific permissions to access Amazon Bedrock AgentCore:

**Required IAM Permissions:**
- `bedrock-agentcore:InvokeAgentRuntime` - To invoke the AgentCore runtime
- `bedrock-agentcore:GetAgentRuntime` - To retrieve runtime information

**Important Notes:**
- The CloudFormation template automatically creates the correct IAM role with these permissions
- The permissions include a wildcard (`*`) suffix to cover sub-resources like `/runtime-endpoint/DEFAULT`
- Without these permissions, the application will fall back to mock responses

**Validation:**
Use the validation script to ensure AgentCore permissions are working:
```bash
./scripts/validate-agentcore.sh --env dev --region us-west-2
```

## Troubleshooting

### Common Issues

1. **Amazon Bedrock AgentCore Access Denied (Mock Responses)**
   ```
   Error: AccessDeniedException when calling InvokeAgentRuntime
   ```
   - Run the validation script: `./scripts/validate-agentcore.sh`
   - Ensure the ECS task role has `bedrock-agentcore:InvokeAgentRuntime` permission
   - Verify the AgentCore ARN is correctly configured in the task definition
   - Check that the IAM policy resource includes the wildcard suffix (`*`)

2. **AgentCore Agent Not Found**
   ```
   Error: Could not find AgentCore endpoint
   ```
   - Ensure your AgentCore agent is deployed
   - Verify the runtime ARN in your .env file
   - Check AWS permissions for Bedrock access

3. **Docker Build Fails**
   ```
   Error: Docker build failed
   ```
   - Ensure Docker is running
   - Check platform compatibility (use linux/amd64 for ECS)
   - Verify network connectivity for package downloads

3. **CloudFormation Stack Fails**
   ```
   Error: ECS stack deployment failed
   ```
   - Check AWS service limits
   - Verify IAM permissions
   - Review CloudFormation events for specific errors

4. **Application Not Accessible**
   - Verify security group configurations
   - Check ALB health checks
   - Review ECS task logs in CloudWatch

### Getting Help

1. **Check Logs**: Use CloudWatch to view application logs
2. **Review Events**: Check CloudFormation stack events for deployment issues
3. **Test Connectivity**: Use the test script to validate deployment health
4. **AWS Support**: Contact AWS support for service-specific issues

## Development

### Project Structure

```
hotel_revenue_optimization_ui/
├── app/                          # Flask application
│   ├── templates/               # HTML templates
│   ├── static/                  # CSS, JS, images
│   └── routes/                  # Application routes
├── scripts/                     # Deployment and test scripts
│   ├── deploy.sh               # Single deployment script
│   └── test.sh                 # Health check script
├── infrastructure/              # Infrastructure as Code
│   ├── cloudformation/         # CloudFormation templates
│   └── docker/                 # Docker build scripts
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── .env.example               # Environment template
└── README.md                  # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally and with deployment
5. Submit a pull request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Include error handling and logging
- Write responsive HTML/CSS

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions, issues, or contributions:
- Create an issue in the repository
- Contact the development team
- Review the troubleshooting section above

---

**Note**: This application requires an active Amazon Bedrock AgentCore agent for full functionality. Ensure your agent is properly deployed and accessible before running the application.
