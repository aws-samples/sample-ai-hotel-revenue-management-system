# CloudFront Deployment Configuration

## Changes Made

### 1. CloudFormation Template Updates (`infrastructure/cloudformation/ecs.yaml`)

**Added CloudFront Distribution:**
- CloudFront distribution with ALB as origin
- Custom origin headers for security (`X-Origin-Verify`)
- Proper cache behaviors for static assets vs dynamic content
- HTTPS redirect and compression enabled
- Price class optimization (PriceClass_100)

**Updated Environment Variables:**
- `SESSION_COOKIE_DOMAIN`: Set to CloudFront domain
- `CLOUDFRONT_DOMAIN`: CloudFront distribution domain
- `AUTH_REDIRECT_URI`: HTTPS callback URL for Cognito

**Updated Outputs:**
- `CloudFrontDomainName`: Distribution domain name
- `CloudFrontDistributionId`: Distribution ID
- `ApplicationURL`: HTTPS application URL

### 2. Cognito Template Updates (`infrastructure/cloudformation/cognito.yaml`)

**Added Parameters:**
- `CloudFrontDomain`: CloudFront distribution domain parameter

**Updated Callback URLs:**
- Primary callback: `https://{CloudFrontDomain}/auth/callback`
- Fallback: localhost URLs for development

**Updated Logout URLs:**
- Primary logout: `https://{CloudFrontDomain}/`
- Fallback: localhost URLs for development

### 3. Deployment Script Updates (`scripts/deploy.sh`)

**Two-Phase Deployment:**
1. Initial Cognito deployment (without CloudFront domain)
2. ECS deployment (creates CloudFront distribution)
3. Cognito update (with CloudFront domain for callbacks)

**Updated Output:**
- Shows CloudFront domain and HTTPS application URL
- Maintains ALB DNS for internal reference

## Security Features

1. **ALB Access Control**: Restricted to CloudFront IP ranges only
2. **Origin Verification**: Custom header validation between CloudFront and ALB
3. **HTTPS Enforcement**: All traffic redirected to HTTPS
4. **Cognito Integration**: Proper callback URLs for authentication flow

## Deployment Command

```bash
./scripts/deploy.sh --env prod --region us-east-1 --agentcore-arn your-arn
```

## Architecture Flow

```
Internet → CloudFront → ALB (with origin header) → ECS Fargate → AgentCore
                ↓
            Cognito Auth (HTTPS callbacks)
```

## Benefits

1. **Global CDN**: Improved performance worldwide
2. **SSL Termination**: Automatic HTTPS with AWS certificate
3. **Caching**: Static assets cached at edge locations
4. **Security**: Origin access control and header validation
5. **Authentication**: Proper HTTPS callbacks for Cognito OAuth flow
