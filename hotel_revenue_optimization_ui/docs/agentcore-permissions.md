# AgentCore Permissions Guide

This document explains the AgentCore permissions configuration for the Hotel Revenue Optimization UI.

## Background

Amazon Bedrock AgentCore uses a different service prefix (`bedrock-agentcore:*`) than regular Bedrock services (`bedrock:*`). The AWS managed policy `AmazonBedrockFullAccess` only covers `bedrock:*` actions, so specific AgentCore permissions must be added separately.

## Required Permissions

The ECS task role needs these specific permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgentRuntime",
        "bedrock-agentcore:GetAgentRuntime"
      ],
      "Resource": "arn:aws:bedrock-agentcore:REGION:ACCOUNT:runtime/AGENT_NAME*"
    }
  ]
}
```

**Important**: The wildcard (`*`) at the end of the resource ARN is crucial because AgentCore creates sub-resources like `/runtime-endpoint/DEFAULT`.

## CloudFormation Implementation

The `infrastructure/cloudformation/ecs.yaml` template includes the correct permissions:

```yaml
ECSTaskRole:
  Type: AWS::IAM::Role
  Properties:
    # ... other properties
    ManagedPolicyArns:
      - arn:aws:iam::aws:policy/AmazonBedrockFullAccess
    Policies:
      - PolicyName: AgentCoreInvokePolicy
        PolicyDocument:
          Version: '2012-10-17'
          Statement:
            - Effect: Allow
              Action:
                - bedrock-agentcore:InvokeAgentRuntime
                - bedrock-agentcore:GetAgentRuntime
              Resource: !Sub '${AgentCoreEndpoint}*'
```

## Symptoms of Missing Permissions

When AgentCore permissions are missing, you'll see:

1. **Application logs show**:
   ```
   AccessDeniedException when calling InvokeAgentRuntime operation: 
   User: arn:aws:sts::ACCOUNT:assumed-role/ROLE/TASK is not authorized 
   to perform: bedrock-agentcore:InvokeAgentRuntime on resource: 
   arn:aws:bedrock-agentcore:REGION:ACCOUNT:runtime/AGENT/runtime-endpoint/DEFAULT
   ```

2. **Application behavior**:
   - Falls back to mock responses
   - No real AI-powered recommendations
   - "Mock response generated" messages in logs

## Validation

Use the validation script to check permissions:

```bash
./scripts/validate-agentcore.sh --env dev --region us-west-2
```

This script checks:
- ✅ ECS service is running
- ✅ Task role has AgentCore permissions
- ✅ AgentCore ARN is configured
- ✅ No recent permission errors in logs

## Manual Verification

You can manually check the permissions:

1. **Get the task role ARN**:
   ```bash
   aws ecs describe-task-definition \
     --task-definition hotel-revenue-optimization-dev:REVISION \
     --query "taskDefinition.taskRoleArn"
   ```

2. **Check attached policies**:
   ```bash
   aws iam list-attached-role-policies --role-name ROLE_NAME
   aws iam list-role-policies --role-name ROLE_NAME
   ```

3. **Verify policy content**:
   ```bash
   aws iam get-role-policy \
     --role-name ROLE_NAME \
     --policy-name AgentCoreInvokePolicy
   ```

## Troubleshooting

### Permission Still Not Working After Update

If you've updated the CloudFormation template but permissions still don't work:

1. **Check task definition revision**: Ensure the ECS service is using the latest task definition
2. **Restart tasks**: Force a new deployment to pick up IAM changes
3. **Verify resource ARN**: Ensure the AgentCore ARN in the policy matches exactly
4. **Check wildcard**: Confirm the resource ARN ends with `*`

### Policy Updates Not Taking Effect

IAM policy changes can take a few minutes to propagate:

1. Wait 2-3 minutes after policy updates
2. Force ECS service deployment to restart tasks
3. Check CloudWatch logs for continued errors

## Best Practices

1. **Always include wildcard**: AgentCore resource ARNs should end with `*`
2. **Use least privilege**: Only grant permissions to the specific AgentCore runtime
3. **Validate after deployment**: Run the validation script after each deployment
4. **Monitor logs**: Watch for AccessDeniedException errors in CloudWatch

## Cross-Region/Account Deployment

When deploying to different regions or accounts:

1. **Update AgentCore ARN**: Ensure the ARN matches your target environment
2. **Verify region**: AgentCore ARN must match the deployment region
3. **Check account ID**: ARN must include the correct AWS account ID
4. **Test permissions**: Run validation script in the new environment

This configuration ensures the application works correctly on first deployment in any AWS region or account.
