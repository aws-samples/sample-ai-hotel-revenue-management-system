#!/bin/bash

# Gateway info from conversation summary
GATEWAY_ARN="arn:aws:bedrock-agentcore:us-east-1:943562114123:gateway/predicthq-gateway"
GATEWAY_URL="https://gateway-predicthq-gateway.bedrock-agentcore.us-east-1.amazonaws.com"
ROLE_ARN="arn:aws:iam::943562114123:role/BedrockAgentCoreRole"

# Create target with inlinePayload as string (not object)
agentcore gateway create-mcp-gateway-target \
  --gateway-arn "$GATEWAY_ARN" \
  --gateway-url "$GATEWAY_URL" \
  --role-arn "$ROLE_ARN" \
  --region us-east-1 \
  --name "predicthq-correct" \
  --target-type "openApiSchema" \
  --target-payload "{\"inlinePayload\": \"$(cat predicthq_correct_schema.json | jq -c .)\"}" \
  --credentials '{"type": "api_key", "api_key": "Bearer jPey4TXh9esggBYAQtkoJ1qtn4PUN-BAKBVIS4K8", "credential_location": "HEADER", "credential_parameter_name": "Authorization"}'

echo "Correct gateway target created!"
