# FaultCast Infrastructure Scripts

Automated scripts for deploying and managing the FaultCast infrastructure.

## Quick Start

### 🚀 Deploy Infrastructure
```bash
cd agent/terraform/scripts
bash deploy.sh
```

### 🗑️ Tear Down Infrastructure
```bash
cd agent/terraform/scripts
bash cleanup.sh
```

## Scripts Overview

### `deploy.sh` ⭐ NEW - Automated Deployment
Complete infrastructure deployment in one command.

**What it does:**
1. Runs `terraform init` (if needed)
2. Creates terraform plan and asks for confirmation
3. Applies terraform configuration
4. Retrieves terraform outputs
5. Updates OpenSearch access policy
6. Creates Knowledge Base via Python script
7. Updates SSM parameter with KB ID
8. Provides next steps for data ingestion

**Usage:**
```bash
cd agent/terraform/scripts
bash deploy.sh
```

**Features:**
- ✅ Fully automated deployment
- ✅ Interactive confirmation before apply
- ✅ Automatic policy updates
- ✅ KB ID auto-detection and SSM update
- ✅ Helpful next steps guidance

---

### `cleanup.sh` ⭐ NEW - Automated Cleanup
Complete infrastructure teardown in one command.

**What it does:**
1. Auto-detects Knowledge Base ID from:
   - SSM Parameter Store
   - Terraform outputs
   - AWS Bedrock API (lists all KBs)
2. Deletes all data sources
3. Deletes Knowledge Base
4. Waits for deletion to complete
5. Runs `terraform destroy`

**Usage:**
```bash
cd agent/terraform/scripts
bash cleanup.sh
```

**Features:**
- ✅ Dynamic KB ID detection (no manual input needed)
- ✅ Graceful handling of missing resources
- ✅ Interactive confirmation before destroy
- ✅ Complete cleanup of all 29 resources

---

### `create_knowledge_base.py`
Python script to create the Bedrock Knowledge Base with OpenSearch Serverless.

**Arguments:**
1. OpenSearch collection ARN
2. Knowledge Base IAM role ARN

**What it does:**
1. Gets collection endpoint from AWS
2. Creates OpenSearch client with SigV4 auth
3. Creates vector index with FAISS engine (dimension: 1024)
4. Creates Bedrock Knowledge Base with Titan embeddings
5. Creates 2 data sources for S3 prefixes:
   - `knowledge-base-inference/`
   - `maintenance-schedules/`

**Usage:**
```bash
python create_knowledge_base.py <collection_arn> <kb_role_arn>
```

**Note:** This is called automatically by `deploy.sh` and `setup_kb.sh`.

---

### `setup_kb.sh` - Legacy KB Setup
Bash script for Knowledge Base setup after Terraform deployment.

**Usage:**
```bash
bash setup_kb.sh
```

**Note:** Use `deploy.sh` instead for a complete automated deployment.

---

## Prerequisites

- Terraform >= 1.0
- Python 3.12+
- AWS CLI configured with appropriate credentials
- Existing S3 bucket: `predictive-maintenance-feature-store`

## Complete Workflow

### Initial Deployment

```bash
# 1. Deploy infrastructure
cd agent/terraform/scripts
bash deploy.sh

# 2. Upload documents to S3 (if needed)
aws s3 cp your-docs/ s3://predictive-maintenance-feature-store/knowledge-base-inference/ --recursive

# 3. Sync Knowledge Base data sources
KB_ID=$(aws ssm get-parameter --name /faultcast/v2/knowledge-base-id --query Parameter.Value --output text --region eu-west-1)
DS_ID=$(aws bedrock-agent list-data-sources --knowledge-base-id $KB_ID --region eu-west-1 --query 'dataSourceSummaries[0].dataSourceId' --output text)
aws bedrock-agent start-ingestion-job --knowledge-base-id $KB_ID --data-source-id $DS_ID --region eu-west-1

# 4. Deploy your agent
cd ../../
agentcore launch
```

### Tear Down

```bash
cd agent/terraform/scripts
bash cleanup.sh
```

## Troubleshooting

### Deploy Script Issues

**Problem:** Terraform outputs not found
```bash
# Solution: Check terraform state
cd agent/terraform
terraform state list
terraform output
```

**Problem:** OpenSearch policy update fails
```bash
# Solution: Wait longer for collection to be ready
sleep 120
bash scripts/deploy.sh
```

**Problem:** KB creation fails with 403
```bash
# Solution: Manually add your IAM user to OpenSearch policy
CURRENT_USER=$(aws sts get-caller-identity --query Arn --output text)
echo "Add this ARN to OpenSearch data access policy: $CURRENT_USER"
```

### Cleanup Script Issues

**Problem:** KB ID not detected
```bash
# Solution: The script will skip KB deletion and proceed with terraform destroy
# This is safe and expected if KB was already deleted
```

**Problem:** Terraform destroy fails
```bash
# Solution: Manually remove problematic resources
terraform state list
terraform state rm <resource>
terraform destroy -var-file=environments/dev/terraform.tfvars
```

### General Issues

**Problem:** Virtual environment errors
```bash
# Solution: Clean and recreate
cd agent/terraform/scripts
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install opensearch-py boto3
```

**Problem:** Index creation fails
```bash
# Solution: Ensure FAISS engine is used (not nmslib)
# This is already configured in create_knowledge_base.py
```

## Configuration

### Modify S3 Prefixes

Edit `create_knowledge_base.py`:
```python
prefixes=['knowledge-base-inference/', 'maintenance-schedules/']
```

### Change Embedding Model

Edit `create_knowledge_base.py`:
```python
'embeddingModelArn': f'arn:aws:bedrock:{region}::foundation-model/amazon.titan-embed-text-v2:0'
```

### Change Region

Edit `agent/terraform/environments/dev/terraform.tfvars`:
```hcl
aws_region = "eu-west-1"
```

## Resources Created

The deployment creates:
- **2 IAM Roles** (AgentCore, Knowledge Base)
- **9 IAM Policies** (inline policies for both roles)
- **1 OpenSearch Serverless Collection** (via CloudFormation)
- **3 OpenSearch Policies** (encryption, network, data access)
- **1 Bedrock Knowledge Base**
- **2 Knowledge Base Data Sources**
- **9 SSM Parameters** (configuration storage)

**Total: 29 resources**

## Notes

- All scripts use color-coded output for better readability
- Scripts include interactive confirmations for safety
- Automatic retry logic for transient AWS API errors
- Comprehensive error messages and next steps
- Scripts are idempotent where possible
- Virtual environment is created automatically
- KB ID is automatically stored in SSM Parameter Store

## Dependencies

Python packages (installed automatically):
- `opensearch-py` - OpenSearch client
- `boto3` - AWS SDK for Python

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error messages
3. Check Terraform state: `terraform state list`
4. Verify AWS credentials: `aws sts get-caller-identity`
