#!/bin/bash
set -e

echo "=== FaultCast Knowledge Base Setup ==="
echo ""

# Get terraform outputs
KB_ROLE_ARN=$(terraform output -raw knowledge_base_role_arn)
COLLECTION_ARN=$(terraform output -raw opensearch_collection_arn)

echo "✅ OpenSearch Collection: $COLLECTION_ARN"
echo "✅ KB Role: $KB_ROLE_ARN"
echo ""

# Get current user ARN
CURRENT_USER_ARN=$(aws sts get-caller-identity --query Arn --output text)
echo "Current user: $CURRENT_USER_ARN"
echo ""

# Update OpenSearch data access policy to include current user
echo "Updating OpenSearch data access policy..."
COLLECTION_NAME="faultcast-kb-v2-dev"

aws opensearchserverless update-access-policy \
  --name "faultcast-kb-v2-access-dev" \
  --type data \
  --policy-version "$(aws opensearchserverless get-access-policy --name faultcast-kb-v2-access-dev --type data --query 'accessPolicyDetail.policyVersion' --output text --region eu-west-1)" \
  --policy "[{\"Rules\":[{\"Resource\":[\"collection/$COLLECTION_NAME\"],\"Permission\":[\"aoss:CreateCollectionItems\",\"aoss:DeleteCollectionItems\",\"aoss:UpdateCollectionItems\",\"aoss:DescribeCollectionItems\"],\"ResourceType\":\"collection\"},{\"Resource\":[\"index/$COLLECTION_NAME/*\"],\"Permission\":[\"aoss:CreateIndex\",\"aoss:DeleteIndex\",\"aoss:UpdateIndex\",\"aoss:DescribeIndex\",\"aoss:ReadDocument\",\"aoss:WriteDocument\"],\"ResourceType\":\"index\"}],\"Principal\":[\"$KB_ROLE_ARN\",\"$CURRENT_USER_ARN\"]}]" \
  --region eu-west-1

echo "✅ Access policy updated"
echo ""
echo "Waiting 60 seconds for policy to propagate..."
sleep 60

# Run Python script
echo "Creating Knowledge Base..."
cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || (python3 -m venv venv && source venv/bin/activate && pip install -q opensearch-py boto3)
python3 create_knowledge_base.py "$COLLECTION_ARN" "$KB_ROLE_ARN"

echo ""
echo "✅ Setup complete!"
