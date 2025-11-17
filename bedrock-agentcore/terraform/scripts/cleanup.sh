#!/bin/bash
set -e

echo "=== FaultCast Infrastructure Cleanup ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGION="eu-west-1"
PROJECT_NAME="faultcast"
ENVIRONMENT="dev"
SSM_PARAM_PATH="/faultcast-v2/knowledge-base-id"

# Navigate to terraform directory
cd "$(dirname "$0")/.."

echo "Detecting Knowledge Base ID..."
echo ""

# Try to get KB ID from SSM parameter first
KB_ID=$(aws ssm get-parameter \
  --name "$SSM_PARAM_PATH" \
  --query 'Parameter.Value' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

if [ -z "$KB_ID" ] || [ "$KB_ID" == "REPLACE_AFTER_KB_CREATION" ]; then
  echo "⚠️  KB ID not found in SSM, checking Terraform state..."
  
  # Try to get from Terraform output
  KB_ID=$(terraform output -raw knowledge_base_id 2>/dev/null || echo "")
  
  if [ -z "$KB_ID" ] || [ "$KB_ID" == "REPLACE_AFTER_KB_CREATION" ]; then
    echo "⚠️  KB ID not found in Terraform output, listing all KBs..."
    
    # List all KBs and filter by name pattern
    KB_ID=$(aws bedrock-agent list-knowledge-bases \
      --region "$REGION" \
      --query "knowledgeBaseSummaries[?contains(name, '${PROJECT_NAME}-kb-v2-${ENVIRONMENT}')].knowledgeBaseId | [0]" \
      --output text 2>/dev/null || echo "")
  fi
fi

if [ -z "$KB_ID" ] || [ "$KB_ID" == "None" ]; then
  echo -e "${YELLOW}⚠️  No Knowledge Base found. Will proceed with Terraform destroy only.${NC}"
  KB_ID=""
else
  echo -e "${GREEN}✅ Found Knowledge Base ID: $KB_ID${NC}"
fi

echo ""
echo -e "${YELLOW}This will delete ALL FaultCast infrastructure resources${NC}"
echo "Region: $REGION"
if [ -n "$KB_ID" ]; then
  echo "Knowledge Base ID: $KB_ID"
fi
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

if [ -n "$KB_ID" ]; then
  echo ""
  echo "=== Step 1: Delete Knowledge Base Data Sources ==="
  echo ""

  # Get data sources for the KB
  DATA_SOURCES=$(aws bedrock-agent list-data-sources \
    --knowledge-base-id "$KB_ID" \
    --region "$REGION" \
    --query 'dataSourceSummaries[].dataSourceId' \
    --output text 2>/dev/null || echo "")

  if [ -n "$DATA_SOURCES" ]; then
    for DS_ID in $DATA_SOURCES; do
      echo "Deleting data source: $DS_ID"
      aws bedrock-agent delete-data-source \
        --knowledge-base-id "$KB_ID" \
        --data-source-id "$DS_ID" \
        --region "$REGION" 2>/dev/null || echo "  ⚠️  Data source already deleted or not found"
    done
    echo -e "${GREEN}✅ Data sources deleted${NC}"
  else
    echo "No data sources found"
  fi

  echo ""
  echo "=== Step 2: Delete Knowledge Base ==="
  echo ""

  aws bedrock-agent delete-knowledge-base \
    --knowledge-base-id "$KB_ID" \
    --region "$REGION" 2>/dev/null && echo -e "${GREEN}✅ Knowledge Base deleted${NC}" || echo "⚠️  Knowledge Base already deleted or not found"

  echo ""
  echo "Waiting 120 seconds for Knowledge Base deletion to complete..."
  sleep 120
else
  echo ""
  echo "=== Skipping Knowledge Base deletion (not found) ==="
  echo ""
fi

echo ""
echo "=== Step 3: Destroy Terraform Resources ==="
echo ""

# Run terraform destroy
terraform destroy \
  -var-file=environments/dev/terraform.tfvars \
  -auto-approve

# Check if agent is deployed
echo ""
echo "=== Checking for deployed agent ==="
echo ""

AGENT_ARN=""

# Try to get agent ARN from SSM
AGENT_ARN=$(aws ssm get-parameter \
  --name "/faultcast/v2/agent-arn" \
  --query 'Parameter.Value' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

if [ -z "$AGENT_ARN" ]; then
  # Try to get from file
  if [ -f "agent_arn.txt" ]; then
    AGENT_ARN=$(cat agent_arn.txt)
  fi
fi

if [ -z "$AGENT_ARN" ]; then
  # Try agentcore status
  AGENT_ARN=$(cd ../../ && agentcore status 2>/dev/null | grep "Agent ARN:" | awk '{print $3}' || echo "")
fi

if [ -n "$AGENT_ARN" ] && [ "$AGENT_ARN" != "None" ]; then
  echo -e "${GREEN}✅ Found deployed agent: $AGENT_ARN${NC}"
  echo ""
  read -p "Do you want to delete the agent? (yes/no): " -r
  echo
  
  if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deleting agent..."
    cd ../../
    
    # Try to delete using agentcore
    if command -v agentcore &> /dev/null; then
      agentcore delete 2>/dev/null || echo "⚠️  Could not delete via agentcore CLI"
    fi
    
    # Also try direct AWS API call
    AGENT_NAME=$(echo "$AGENT_ARN" | awk -F'/' '{print $NF}')
    aws bedrock-agentcore delete-agent-runtime \
      --agent-runtime-arn "$AGENT_ARN" \
      --region "$REGION" 2>/dev/null && echo -e "${GREEN}✅ Agent deleted${NC}" || echo "⚠️  Agent may already be deleted"
    
    # Delete SSM parameter
    aws ssm delete-parameter \
      --name "/faultcast/v2/agent-arn" \
      --region "$REGION" 2>/dev/null || echo "⚠️  SSM parameter already deleted"
    
    # Delete agent ARN file
    rm -f terraform/agent_arn.txt
    
    cd terraform
    echo ""
  else
    echo "Skipping agent deletion"
    echo ""
  fi
else
  echo "No deployed agent found"
  echo ""
fi

echo ""
echo -e "${GREEN}=== Cleanup Complete ===${NC}"
echo ""
echo "All resources have been destroyed:"
if [ -n "$AGENT_ARN" ]; then
  echo "  ✅ Agent runtime"
fi
echo "  ✅ Knowledge Base and data sources"
echo "  ✅ OpenSearch Serverless collection"
echo "  ✅ IAM roles and policies"
echo "  ✅ SSM parameters"
echo ""
