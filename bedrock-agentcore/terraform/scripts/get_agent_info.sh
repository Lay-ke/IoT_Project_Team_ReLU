#!/bin/bash

# FaultCast Agent Information Script
# Quick script for team members to get agent connection details

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

REGION="eu-west-1"

echo ""
echo -e "${BLUE}=== FaultCast Agent Information ===${NC}"
echo ""

# Get Knowledge Base ID
KB_ID=$(aws ssm get-parameter \
  --name "/faultcast/v2/knowledge-base-id" \
  --query 'Parameter.Value' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "Not found")

# Get Agent ARN
AGENT_ARN=$(aws ssm get-parameter \
  --name "/faultcast/v2/agent-arn" \
  --query 'Parameter.Value' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

if [ -z "$AGENT_ARN" ]; then
  # Try from file
  SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
  if [ -f "$SCRIPT_DIR/../agent_arn.txt" ]; then
    AGENT_ARN=$(cat "$SCRIPT_DIR/../agent_arn.txt")
  else
    AGENT_ARN="Not found"
  fi
fi

# Get AgentCore Role ARN
AGENTCORE_ROLE=$(aws ssm get-parameter \
  --name "/faultcast/v2/agentcore-role-arn" \
  --query 'Parameter.Value' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

if [ -z "$AGENTCORE_ROLE" ]; then
  # Try from terraform
  cd "$(dirname "$0")/.."
  AGENTCORE_ROLE=$(terraform output -raw agentcore_execution_role_arn 2>/dev/null || echo "Not found")
fi

# Display information
echo -e "${GREEN}Region:${NC} $REGION"
echo -e "${GREEN}Knowledge Base ID:${NC} $KB_ID"
echo -e "${GREEN}Agent ARN:${NC} $AGENT_ARN"
echo -e "${GREEN}AgentCore Role ARN:${NC} $AGENTCORE_ROLE"
echo ""

# Show how to invoke
if [ "$AGENT_ARN" != "Not found" ]; then
  echo -e "${BLUE}=== How to Invoke the Agent ===${NC}"
  echo ""
  echo "Using agentcore CLI:"
  echo -e "${YELLOW}  agentcore invoke '{\"prompt\": \"What is the status of conveyor-A001?\"}' ${NC}"
  echo ""
  echo "Using Python (boto3):"
  echo -e "${YELLOW}  import boto3, json"
  echo "  client = boto3.client('bedrock-agentcore', region_name='$REGION')"
  echo "  response = client.invoke_agent_runtime("
  echo "      agentRuntimeArn='$AGENT_ARN',"
  echo "      runtimeSessionId='session-123',"
  echo "      payload=json.dumps({'prompt': 'Hello'}).encode()"
  echo "  )"
  echo "  print(json.loads(response['response'].read()))${NC}"
  echo ""
  echo "Using AWS CLI:"
  echo -e "${YELLOW}  aws bedrock-agentcore invoke-agent-runtime \\"
  echo "    --agent-runtime-arn '$AGENT_ARN' \\"
  echo "    --runtime-session-id 'session-123' \\"
  echo "    --payload '{\"prompt\": \"Hello\"}' \\"
  echo "    --region $REGION \\"
  echo "    output.json${NC}"
  echo ""
fi

# Show environment variables for easy export
echo -e "${BLUE}=== Environment Variables ===${NC}"
echo ""
echo "Export these for easy access:"
echo -e "${YELLOW}export FAULTCAST_REGION='$REGION'${NC}"
echo -e "${YELLOW}export FAULTCAST_KB_ID='$KB_ID'${NC}"
echo -e "${YELLOW}export FAULTCAST_AGENT_ARN='$AGENT_ARN'${NC}"
echo -e "${YELLOW}export FAULTCAST_ROLE_ARN='$AGENTCORE_ROLE'${NC}"
echo ""

# Save to .env file
echo "Save to .env file? (yes/no): "
read -r REPLY
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
  ENV_FILE="$(dirname "$0")/../../.env.agent"
  cat > "$ENV_FILE" << EOF
# FaultCast Agent Configuration
# Generated: $(date)

FAULTCAST_REGION=$REGION
FAULTCAST_KB_ID=$KB_ID
FAULTCAST_AGENT_ARN=$AGENT_ARN
FAULTCAST_ROLE_ARN=$AGENTCORE_ROLE

# AWS Configuration
AWS_DEFAULT_REGION=$REGION
KNOWLEDGE_BASE_ID=$KB_ID
KNOWLEDGE_BASE_REGION=$REGION
EOF
  echo -e "${GREEN}✅ Configuration saved to: $ENV_FILE${NC}"
  echo ""
  echo "Load with: source $ENV_FILE"
  echo ""
fi

# Show logs command
if [ "$AGENT_ARN" != "Not found" ]; then
  AGENT_NAME=$(echo "$AGENT_ARN" | awk -F'/' '{print $NF}')
  echo -e "${BLUE}=== View Agent Logs ===${NC}"
  echo ""
  echo -e "${YELLOW}aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_NAME}-DEFAULT \\"
  echo "  --log-stream-name-prefix '2025/10/22/[runtime-logs]' \\"
  echo "  --follow \\"
  echo "  --region $REGION${NC}"
  echo ""
fi

echo -e "${BLUE}=== Additional Resources ===${NC}"
echo ""
echo "View all SSM parameters:"
echo -e "${YELLOW}  aws ssm get-parameters-by-path --path /faultcast/v2/ --region $REGION${NC}"
echo ""
echo "Check agent status:"
echo -e "${YELLOW}  agentcore status${NC}"
echo ""
echo "View GenAI Dashboard:"
echo -e "${YELLOW}  https://console.aws.amazon.com/cloudwatch/home?region=$REGION#gen-ai-observability/agent-core${NC}"
echo ""
