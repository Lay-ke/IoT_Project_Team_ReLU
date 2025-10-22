#!/bin/bash
# Full Stack Deployment Script - PMF (Predictive Maintenance Forecaster)
# Destroys existing infrastructure and redeploys with AgentCore

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AGENT_DIR="agent"
IAC_DIR="IAC"
TERRAFORM_AGENT_DIR="$AGENT_DIR/terraform"
VENV_NAME="faultcast-env"

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}  PMF Full Stack Deployment - Destroy & Reprovision${NC}"
echo -e "${BLUE}======================================================================${NC}"

# Step 1: Destroy existing infrastructure
echo -e "\n${YELLOW}Step 1: Destroying existing infrastructure...${NC}"
echo -e "${RED}WARNING: This will destroy all existing resources!${NC}"
read -p "Continue? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Destroy Agent infrastructure
if [ -d "$TERRAFORM_AGENT_DIR" ]; then
    echo -e "\n${YELLOW}Destroying Agent infrastructure...${NC}"
    cd "$TERRAFORM_AGENT_DIR"
    terraform destroy -auto-approve || echo -e "${RED}Agent destroy failed (may not exist)${NC}"
    cd - > /dev/null
fi

# Destroy IAC infrastructure
if [ -d "$IAC_DIR" ]; then
    echo -e "\n${YELLOW}Destroying IAC infrastructure...${NC}"
    cd "$IAC_DIR"
    terraform destroy -auto-approve || echo -e "${RED}IAC destroy failed (may not exist)${NC}"
    cd - > /dev/null
fi

echo -e "${GREEN}✓ Infrastructure destroyed${NC}"

# Step 2: Setup Python environment
echo -e "\n${YELLOW}Step 2: Setting up Python environment...${NC}"

if [ ! -d "$VENV_NAME" ]; then
    python3 -m venv "$VENV_NAME"
fi

source "$VENV_NAME/bin/activate"

# Install AgentCore SDK and requirements
pip install -q --upgrade pip
pip install -q bedrock-agentcore bedrock-agentcore-starter-toolkit
pip install -q -r "$AGENT_DIR/agentcore-requirements.txt"

echo -e "${GREEN}✓ Python environment ready${NC}"

# Step 3: Deploy Agent infrastructure (IAM, Knowledge Base, SSM)
echo -e "\n${YELLOW}Step 3: Deploying Agent infrastructure...${NC}"

cd "$TERRAFORM_AGENT_DIR"
terraform init
terraform apply -auto-approve

# Capture outputs
AGENTCORE_ROLE_ARN=$(terraform output -raw agentcore_execution_role_arn 2>/dev/null || echo "")
KB_ID=$(terraform output -raw knowledge_base_id 2>/dev/null || echo "")

cd - > /dev/null

echo -e "${GREEN}✓ Agent infrastructure deployed${NC}"
echo -e "  AgentCore Role: ${AGENTCORE_ROLE_ARN}"
echo -e "  Knowledge Base ID: ${KB_ID}"

# Step 4: Deploy to Bedrock AgentCore
echo -e "\n${YELLOW}Step 4: Deploying agent to Bedrock AgentCore...${NC}"

cd "$AGENT_DIR"

# Configure AgentCore
echo -e "${BLUE}Configuring AgentCore...${NC}"
agentcore configure --entrypoint faultcast_agentcore.py

# Launch to AWS
echo -e "${BLUE}Launching to AWS Bedrock AgentCore...${NC}"
agentcore launch

# Capture agent details
AGENT_ID=$(grep 'agent_id:' .bedrock_agentcore.yaml | awk '{print $2}' || echo "")
AGENT_ARN=$(grep 'agent_arn:' .bedrock_agentcore.yaml | awk '{print $2}' || echo "")

cd - > /dev/null

echo -e "${GREEN}✓ AgentCore deployment complete${NC}"
echo -e "  Agent ID: ${AGENT_ID}"
echo -e "  Agent ARN: ${AGENT_ARN}"

# Step 5: Deploy IAC infrastructure (IoT, Lambda, SageMaker)
echo -e "\n${YELLOW}Step 5: Deploying IAC infrastructure...${NC}"

cd "$IAC_DIR"

# Update bedrock_agent_arn in variables if needed
if [ -n "$AGENT_ARN" ]; then
    echo -e "${BLUE}Updating Bedrock Agent ARN in IAC...${NC}"
    # This assumes you have a tfvars file or will pass it as variable
    export TF_VAR_bedrock_agent_arn="$AGENT_ARN"
fi

terraform init
terraform apply -auto-approve

cd - > /dev/null

echo -e "${GREEN}✓ IAC infrastructure deployed${NC}"

# Step 6: Verification
echo -e "\n${YELLOW}Step 6: Verifying deployment...${NC}"

# Test AgentCore
echo -e "${BLUE}Testing AgentCore agent...${NC}"
cd "$AGENT_DIR"
agentcore invoke '{"prompt": "Hello, are you operational?"}' || echo -e "${RED}Agent test failed${NC}"
cd - > /dev/null

echo -e "\n${BLUE}======================================================================${NC}"
echo -e "${GREEN}✅ Full Stack Deployment Complete!${NC}"
echo -e "${BLUE}======================================================================${NC}"

echo -e "\n${GREEN}Deployment Summary:${NC}"
echo -e "  ${BLUE}Agent Infrastructure:${NC}"
echo -e "    - AgentCore Role: ${AGENTCORE_ROLE_ARN}"
echo -e "    - Knowledge Base: ${KB_ID}"
echo -e "    - Agent ID: ${AGENT_ID}"
echo -e "    - Agent ARN: ${AGENT_ARN}"
echo -e "\n  ${BLUE}IAC Infrastructure:${NC}"
echo -e "    - IoT Core: Deployed"
echo -e "    - Lambda Functions: Deployed"
echo -e "    - SageMaker: Deployed"

echo -e "\n${GREEN}Next Steps:${NC}"
echo -e "  1. Test agent invocation:"
echo -e "     ${BLUE}cd agent && agentcore invoke '{\"prompt\": \"Check conveyor-A001\"}'${NC}"
echo -e "\n  2. View CloudWatch logs for agent execution"
echo -e "\n  3. Start the frontend dashboard:"
echo -e "     ${BLUE}cd frontend && npm install && npm run dev${NC}"
echo -e "\n  4. Monitor IoT data flow in AWS Console"

echo -e "\n${BLUE}======================================================================${NC}"
