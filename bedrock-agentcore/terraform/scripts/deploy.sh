#!/bin/bash
set -e

echo "=== FaultCast Infrastructure Deployment ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGION="eu-west-1"
PROJECT_NAME="faultcast"
ENVIRONMENT="dev"

# Navigate to terraform directory
cd "$(dirname "$0")/.."

echo -e "${BLUE}Deployment Configuration:${NC}"
echo "Region: $REGION"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo ""

# Check if terraform is initialized
if [ ! -d ".terraform" ]; then
  echo -e "${YELLOW}Terraform not initialized. Running terraform init...${NC}"
  terraform init
  echo ""
fi

echo "=== Step 1: Terraform Plan ==="
echo ""

# Run terraform plan
terraform plan \
  -var-file=environments/dev/terraform.tfvars \
  -out=tfplan

echo ""
read -p "Do you want to apply this plan? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Deployment cancelled."
    rm -f tfplan
    exit 0
fi

echo ""
echo "=== Step 2: Terraform Apply ==="
echo ""

# Apply terraform
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}✅ Terraform resources created${NC}"
echo ""

# Get terraform outputs
echo "=== Step 3: Retrieving Terraform Outputs ==="
echo ""

KB_ROLE_ARN=$(terraform output -raw knowledge_base_role_arn 2>/dev/null || echo "")
COLLECTION_ARN=$(terraform output -raw opensearch_collection_arn 2>/dev/null || echo "")
AGENTCORE_ROLE_ARN=$(terraform output -raw agentcore_execution_role_arn 2>/dev/null || echo "")

if [ -z "$KB_ROLE_ARN" ] || [ -z "$COLLECTION_ARN" ]; then
  echo -e "${RED}❌ Failed to retrieve terraform outputs${NC}"
  echo "KB Role ARN: $KB_ROLE_ARN"
  echo "Collection ARN: $COLLECTION_ARN"
  exit 1
fi

echo -e "${GREEN}✅ Terraform outputs retrieved${NC}"
echo "KB Role ARN: $KB_ROLE_ARN"
echo "Collection ARN: $COLLECTION_ARN"
echo "AgentCore Role ARN: $AGENTCORE_ROLE_ARN"
echo ""

echo "=== Step 4: Setting up Knowledge Base ==="
echo ""

# Get current user ARN for OpenSearch access
CURRENT_USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
echo "Current user: $CURRENT_USER_ARN"
echo ""

# Update OpenSearch data access policy
echo "Updating OpenSearch data access policy..."
COLLECTION_NAME="${PROJECT_NAME}-kb-v2-${ENVIRONMENT}"

# Get current policy version
POLICY_VERSION=$(aws opensearchserverless get-access-policy \
  --name "${PROJECT_NAME}-kb-v2-access-${ENVIRONMENT}" \
  --type data \
  --query 'accessPolicyDetail.policyVersion' \
  --output text \
  --region "$REGION" 2>/dev/null || echo "")

if [ -z "$POLICY_VERSION" ]; then
  echo -e "${RED}❌ Failed to get OpenSearch policy version${NC}"
  exit 1
fi

# Update the policy to include current user
aws opensearchserverless update-access-policy \
  --name "${PROJECT_NAME}-kb-v2-access-${ENVIRONMENT}" \
  --type data \
  --policy-version "$POLICY_VERSION" \
  --policy "[{\"Rules\":[{\"Resource\":[\"collection/$COLLECTION_NAME\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:DeleteCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DescribeCollectionItems\"],\"ResourceType\":\"collection\"},{\"Resource\":[\"index/$COLLECTION_NAME/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:DeleteIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"],\"ResourceType\":\"index\"}],\"Principal\":[\"$KB_ROLE_ARN\",\"$CURRENT_USER_ARN\"]}]" \
  --region "$REGION"

echo -e "${GREEN}✅ OpenSearch access policy updated${NC}"
echo ""
echo "Waiting 60 seconds for policy to propagate..."
sleep 60

echo ""
echo "=== Step 5: Creating Knowledge Base ==="
echo ""

# Navigate to scripts directory and run KB creation
cd scripts

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
  pip install -q opensearch-py boto3
else
  source venv/bin/activate
fi

# Run the KB creation script
python3 create_knowledge_base.py "$COLLECTION_ARN" "$KB_ROLE_ARN"

# Get the created KB ID
KB_ID=$(aws bedrock-agent list-knowledge-bases \
  --region "$REGION" \
  --query "knowledgeBaseSummaries[?contains(name, '${PROJECT_NAME}-kb-v2-${ENVIRONMENT}')].knowledgeBaseId | [0]" \
  --output text 2>/dev/null || echo "")

if [ -z "$KB_ID" ] || [ "$KB_ID" == "None" ]; then
  echo -e "${RED}❌ Failed to retrieve Knowledge Base ID${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}✅ Knowledge Base created: $KB_ID${NC}"
echo ""

# Update SSM parameters
echo "=== Step 6: Updating SSM Parameters ==="
echo ""

aws ssm put-parameter \
  --name "/faultcast/v2/knowledge-base-id" \
  --value "$KB_ID" \
  --type "String" \
  --overwrite \
  --region "$REGION"

echo -e "${GREEN}✅ SSM parameter updated with KB ID${NC}"

# Save AgentCore role ARN to SSM for agent deployment
aws ssm put-parameter \
  --name "/faultcast/v2/agentcore-role-arn" \
  --value "$AGENTCORE_ROLE_ARN" \
  --type "String" \
  --overwrite \
  --region "$REGION"

echo -e "${GREEN}✅ SSM parameter updated with AgentCore role ARN${NC}"
echo ""

# Navigate back to terraform directory
cd ..

echo ""
echo -e "${GREEN}=== Infrastructure Deployment Complete ===${NC}"
echo ""
echo "Infrastructure Summary:"
echo "  ✅ IAM Roles and Policies"
echo "  ✅ OpenSearch Serverless Collection"
echo "  ✅ Knowledge Base: $KB_ID"
echo "  ✅ SSM Parameters"
echo ""

# Ask if user wants to deploy the agent
echo -e "${YELLOW}Do you want to deploy the FaultCast agent now?${NC}"
read -p "Deploy agent? (yes/no): " -r
echo

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
  echo ""
  echo "=== Step 7: Deploying FaultCast Agent ==="
  echo ""
  
  # Navigate to agent directory
  cd ../../
  
  # Check if agentcore is available
  if ! command -v agentcore &> /dev/null; then
    echo -e "${RED}❌ agentcore CLI not found${NC}"
    echo "Please install bedrock-agentcore-starter-toolkit:"
    echo "  pip install bedrock-agentcore-starter-toolkit"
    exit 1
  fi
  
  # Generate agentcore config from template with Terraform values
  echo "Generating agentcore config from Terraform outputs..."
  
  if [ ! -f ".bedrock_agentcore.yaml.template" ]; then
    echo -e "${RED}❌ Template file not found: .bedrock_agentcore.yaml.template${NC}"
    exit 1
  fi
  
  # Get AWS account ID
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
  
  # Get current directory for paths
  AGENT_DIR=$(pwd)
  AGENT_ENTRYPOINT="$AGENT_DIR/faultcast_agentcore.py"
  
  # Generate ECR repository name
  ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/bedrock-agentcore-relu_agent"
  
  # Backup existing config if it exists
  if [ -f ".bedrock_agentcore.yaml" ]; then
    cp .bedrock_agentcore.yaml .bedrock_agentcore.yaml.backup
    echo "  ✅ Backed up existing config to .bedrock_agentcore.yaml.backup"
  fi
  
  # Generate new config from template
  sed -e "s|{{AGENT_ENTRYPOINT}}|$AGENT_ENTRYPOINT|g" \
      -e "s|{{SOURCE_PATH}}|$AGENT_DIR|g" \
      -e "s|{{EXECUTION_ROLE_ARN}}|$AGENTCORE_ROLE_ARN|g" \
      -e "s|{{AWS_ACCOUNT_ID}}|$AWS_ACCOUNT_ID|g" \
      -e "s|{{AWS_REGION}}|$REGION|g" \
      -e "s|{{ECR_REPOSITORY}}|$ECR_REPOSITORY|g" \
      .bedrock_agentcore.yaml.template > .bedrock_agentcore.yaml
  
  echo -e "${GREEN}✅ Generated agentcore config with Terraform values${NC}"
  echo "  Execution Role: $AGENTCORE_ROLE_ARN"
  echo "  Region: $REGION"
  echo "  ECR Repository: $ECR_REPOSITORY"
  echo ""
  
  # Deploy the agent
  echo "Deploying agent to AWS Bedrock AgentCore Runtime..."
  agentcore launch
  
  # Get the agent ARN
  AGENT_ARN=$(agentcore status 2>/dev/null | grep "Agent ARN:" | awk '{print $3}' || echo "")
  
  if [ -z "$AGENT_ARN" ]; then
    echo -e "${YELLOW}⚠️  Could not automatically detect agent ARN${NC}"
    echo "Please run: agentcore status"
  else
    echo ""
    echo -e "${GREEN}✅ Agent deployed successfully${NC}"
    echo "Agent ARN: $AGENT_ARN"
    
    # Save agent ARN to a file for team access
    echo "$AGENT_ARN" > terraform/agent_arn.txt
    echo ""
    echo -e "${GREEN}✅ Agent ARN saved to: terraform/agent_arn.txt${NC}"
    
    # Also save to SSM for programmatic access
    aws ssm put-parameter \
      --name "/faultcast/v2/agent-arn" \
      --value "$AGENT_ARN" \
      --type "String" \
      --overwrite \
      --region "$REGION" 2>/dev/null && echo -e "${GREEN}✅ Agent ARN saved to SSM: /faultcast/v2/agent-arn${NC}" || echo -e "${YELLOW}⚠️  Could not save to SSM${NC}"
  fi
  
  echo ""
  echo -e "${GREEN}=== Complete Deployment Finished ===${NC}"
  echo ""
  echo "Deployment Summary:"
  echo "  ✅ Infrastructure (Terraform)"
  echo "  ✅ Knowledge Base: $KB_ID"
  echo "  ✅ Agent: $AGENT_ARN"
  echo ""
  echo -e "${BLUE}Team Access Information:${NC}"
  echo "  Knowledge Base ID: $KB_ID"
  echo "  Agent ARN: $AGENT_ARN"
  echo "  Region: $REGION"
  echo ""
  echo "  Retrieve anytime with:"
  echo "    KB_ID=\$(aws ssm get-parameter --name /faultcast/v2/knowledge-base-id --query Parameter.Value --output text --region $REGION)"
  echo "    AGENT_ARN=\$(aws ssm get-parameter --name /faultcast/v2/agent-arn --query Parameter.Value --output text --region $REGION)"
  echo ""
else
  echo ""
  echo -e "${GREEN}=== Infrastructure Deployment Complete ===${NC}"
  echo ""
  echo "Infrastructure Summary:"
  echo "  ✅ IAM Roles and Policies"
  echo "  ✅ OpenSearch Serverless Collection"
  echo "  ✅ Knowledge Base: $KB_ID"
  echo "  ✅ SSM Parameters"
  echo ""
  echo -e "${BLUE}Next Steps:${NC}"
  echo "1. Upload documents to S3 (if needed):"
  echo "   aws s3 cp your-docs/ s3://predictive-maintenance-feature-store/knowledge-base-inference/ --recursive"
  echo ""
  echo "2. Sync Knowledge Base data sources:"
  echo "   KB_ID=$KB_ID"
  echo "   DS_ID=\$(aws bedrock-agent list-data-sources --knowledge-base-id \$KB_ID --region $REGION --query 'dataSourceSummaries[0].dataSourceId' --output text)"
  echo "   aws bedrock-agent start-ingestion-job --knowledge-base-id \$KB_ID --data-source-id \$DS_ID --region $REGION"
  echo ""
  echo "3. Deploy your agent:"
  echo "   cd agent"
  echo "   agentcore launch"
  echo ""
fi

echo -e "${BLUE}Useful Commands:${NC}"
echo "  terraform output                    # View all outputs"
echo "  terraform state list                # List all resources"
echo "  agentcore status                    # Check agent status"
echo "  agentcore invoke '{\"prompt\": \"test\"}' # Test agent"
echo "  bash scripts/cleanup.sh             # Tear down everything"
echo ""
