# Deployment Changes Summary

## CloudFormation Template Updates (ecs.yaml)

### 1. CloudFront Timeout Configuration
- **Added**: `OriginReadTimeout: 60` (maximum allowed)
- **Added**: `OriginKeepaliveTimeout: 60` (maximum allowed)
- **Location**: CloudFront CustomOriginConfig section

### 2. ALB Timeout Configuration  
- **Updated**: `idle_timeout.timeout_seconds` from `90` to `60`
- **Location**: ALB LoadBalancerAttributes section

### 3. ECS Container Timeout Configuration
- **Added**: `StartTimeout: 60` (container startup timeout)
- **Added**: `StopTimeout: 60` (graceful shutdown timeout)  
- **Location**: ECS TaskDefinition ContainerDefinitions section

## Application Code Updates

### 1. Authentication Fix (app/config.py)
- **Added**: `COGNITO_CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET', '')`
- **Issue**: Missing config caused fallback to hardcoded secret

### 2. Logout URL Fix (app/auth/cognito.py)
- **Changed**: `logout_uri` parameter to `redirect_uri` in Cognito logout URL
- **Issue**: Cognito expects `redirect_uri` not `logout_uri`

### 3. Print/Save Functionality Fix (templates)
- **Updated**: Both `natural_language.html` and `structured_form.html`
- **Changed**: `window.print()` to `printResults()` function
- **Added**: JavaScript function that only captures results section
- **Issue**: Was printing entire page including sample hotel profiles

### 4. UI Branding Update (app/templates/base.html)
- **Changed**: Copyright from "Hotel Revenue Optimization" to "Zenith Stays Group"

## Infrastructure Alignment

All timeout configurations are now aligned at **60 seconds**:
- CloudFront Origin Read Timeout: 60s (AWS maximum)
- ALB Idle Timeout: 60s  
- ECS Container Start/Stop: 60s
- Target Group Health Checks: 5s timeout, 30s interval (industry standard)

## Deployment Status

✅ **All changes deployed and active**
- CloudFormation templates updated with timeout configurations
- Application code fixes deployed via Docker image
- Infrastructure changes applied via CLI and will be maintained by CF template
- Cache invalidated for immediate effect

## Future Deployments

The updated CloudFormation templates ensure that:
1. New deployments will automatically include timeout configurations
2. No manual CLI commands needed for timeout settings
3. All authentication and UI fixes are preserved
4. Infrastructure remains consistent across environments
