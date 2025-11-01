# AI-Powered Hotel Revenue Optimization System

An intelligent multi-agent system that leverages Amazon Bedrock AgentCore and CrewAI to optimize hotel room pricing and maximize revenue through AI-driven analysis and recommendations.

## Overview

This system combines advanced AI agents with real-time market analysis to provide hotel managers with actionable insights for revenue optimization. It analyzes competitor pricing, demand patterns, local events, and historical booking data to deliver precise pricing recommendations and revenue forecasts.

## Key Features

- **Multi-Agent AI Architecture**: Specialized agents for demand forecasting, pricing optimization, and market analysis
- **Real-Time Market Intelligence**: Competitor pricing analysis and market trend monitoring  
- **Demand Forecasting**: Predictive analytics for occupancy and revenue projections
- **Interactive Web Interface**: User-friendly dashboard for natural language queries and structured forms
- **AWS Integration**: Built on Amazon Bedrock AgentCore with support for Nova and Claude models
- **Production Ready**: Fully deployed system with comprehensive monitoring and observability

## Components

### Core AI Agent System (`hotel_revenue_optimization/`)
Multi-agent AI solution leveraging CrewAI and Amazon Bedrock AgentCore for revenue optimization:
- **Version**: 2.1.0 - Production Ready
- **Models**: Amazon Nova (Premier, Pro, Lite, Micro), Anthropic Claude (3.7 Sonnet, 3.5 Haiku, 3 Haiku)
- **Provider Options**: AMAZON (default), ANTHROPIC, HYBRID
- **Performance**: 46-52 seconds execution time (AWS environment)
- **Input Formats**: Natural language, structured JSON, prompt-based
- **Deployment**: AWS Bedrock AgentCore with Docker containerization

### Web UI (`hotel_revenue_optimization_ui/`)
Modern Flask-based web interface for hotel managers:
- **Features**: Natural language queries, structured forms, query history
- **Authentication**: AWS Cognito User Pools
- **Deployment**: ECS Fargate with Application Load Balancer
- **Infrastructure**: VPC, CloudFront CDN, CloudWatch monitoring
- **Security**: IAM roles, security groups, secrets management

### Knowledge Base
- Historical booking data and pricing patterns
- Competitor pricing information
- Local events and seasonal patterns
- Revenue management best practices

### AWS Infrastructure
- CloudFormation templates for automated deployment
- Container registry (ECR) for Docker images
- Monitoring and logging with CloudWatch

## Quick Start

### Core AI Agent
```bash
cd hotel_revenue_optimization
pip install -e .
# Configure environment variables in .env
python -m src.hotel_revenue_optimization.main
```

### Web UI
```bash
cd hotel_revenue_optimization_ui
./scripts/deploy.sh --env dev --region us-west-2
# Or run locally
flask run --debug
```

For detailed setup and deployment instructions, see the README files in each component directory.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

