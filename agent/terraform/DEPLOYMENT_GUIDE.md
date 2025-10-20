# FaultCast Terraform Deployment Guide

## Complete Infrastructure Deployment

This guide covers deploying the complete FaultCast infrastructure including Knowledge Base, IAM roles, S3 buckets, and SSM parameters.

## What Gets Created

### 1. Knowledge Base Infrastructure
- **Bedrock Knowledge Base**: Vector database for maintenance playbooks
- **OpenSearch Serverless Collection**: Vector search backend
- **S3 Bucket**: Storage for Knowledge Base documents
- **IAM Role**: Knowledge Base execution role with permissions for:
  - S3 access (read documents)
  - Bedrock model invocation (embeddings)
  - OpenSearch Serverless access

### 2. AgentCore Infrastructure
- **IAM Execution Role**: AgentCore runtime role with permissions for:
  - SSM Parameter Store access
  - S3 read/write access (work schedules)
  - Bedrock Knowledge Base access (retrieve)
  - Bedrock model invocation (Nova Pro)

### 3. Storage Infrastructure
- **Work Schedules S3 Bucket**: Storage for generated work schedules
  - Versioning enabled
  - Encryption enabled
  - Lifecycle policies (90 days → Glacier, 365 days → Delete)

### 4. Configuration Management
- **SSM Parameters**: Runtime configuration
  - `/faultcast/knowledge-base-id`
  - `/faultcast/knowledge-base-region`
  - `/faultcast/work-schedule-bucket`
  - `/faultcast/work-schedule-prefix`

## Prerequisites

1. **AWS CLI** configured with credentials
2. **Terraform** >= 1.0 installed
3. **AWS Permissions** for:
   - IAM (roles, policies)
   - S3 (buckets, objects)
   - SSM (parameters)
   - Bedrock (Knowledge Base, models)
   - OpenSearch Serverless (collections, policies)

## Step-by-Step Deployment

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

This will download required providers:
- AWS provider
- OpenSearch Serverless provider

### Step 2: Configure Variables

Edit `environments/dev/terraform.tfvars`:

```hcl
# Create new Knowledge Base
create_knowledge_base = true

# OR use existing Knowledge Base
# create_knowledge_base = false
# knowledge_base_id = "YOUR_EXISTING_KB_ID"

# Other configurations
sagemaker_endpoint_name = "your-sagemaker-endpoint"
```

### Step 3: Plan Deployment

```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

Review the plan to see what will be created:
- 1 Knowledge Base
- 1 OpenSearch Serverless Collection
- 3 Security Policies (encryption, network, data access)
- 2 S3 Buckets (KB docs, work schedules)
- 2 IAM Roles (KB role, AgentCore role)
- 4 SSM Parameters
- 1 Data Source

### Step 4: Apply Configuration

```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

Type `yes` when prompted.

**Deployment time**: ~5-10 minutes

### Step 5: Upload Knowledge Base Documents

After deployment, upload your maintenance playbooks to the Knowledge Base S3 bucket:

```bash
# Get the bucket name from Terraform output
KB_BUCKET=$(terraform output -raw knowledge_base_s3_bucket)

# Upload playbook
aws s3 cp ../playbook.md s3://$KB_BUCKET/playbooks/

# Upload prediction history (if you have it)
aws s3 cp prediction_history/ s3://$KB_BUCKET/predictions/ --recursive
```

### Step 6: Sync Knowledge Base

After uploading documents, trigger a sync:

```bash
# Get Knowledge Base ID and Data Source ID
KB_ID=$(terraform output -raw knowledge_base_id)
DS_ID=$(terraform output -raw knowledge_base_data_source_id)

# Start ingestion job
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region eu-west-1
```

Monitor the ingestion:

```bash
aws bedrock-agent list-ingestion-jobs \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region eu-west-1
```

### Step 7: Deploy AgentCore Agent

Now deploy the agent using the AgentCore CLI:

```bash
cd ..

# Configure agent
agentcore configure --entrypoint faultcast_agentcore.py

# When prompted, use the IAM role created by Terraform
# Get the role ARN:
terraform -chdir=terraform output -raw agentcore_execution_role_arn

# Deploy agent
agentcore launch
```

### Step 8: Verify Deployment

Test the complete system:

```bash
# Test agent invocation
agentcore invoke '{"prompt": "What are the maintenance procedures for pulley faults?"}'

# Test with ML prediction
agentcore invoke '{
  "machine_id": "conveyor-A001",
  "prediction": {
    "predicted_class": "pulley",
    "confidence": 0.961,
    "top_k": {
      "pulley": 0.961,
      "normal": 0.025
    }
  }
}'

# Check work schedule was created
WORK_BUCKET=$(terraform -chdir=terraform output -raw work_schedule_bucket_name)
aws s3 ls s3://$WORK_BUCKET/maintenance-schedules/
```

## Terraform Outputs

After deployment, get important values:

```bash
# Knowledge Base ID
terraform output knowledge_base_id

# Knowledge Base S3 Bucket
terraform output knowledge_base_s3_bucket

# Work Schedule Bucket
terraform output work_schedule_bucket_name

# AgentCore Execution Role ARN
terraform output agentcore_execution_role_arn

# All outputs
terraform output
```

## IAM Roles Created

### 1. Knowledge Base Role
**Name**: `faultcast-kb-role-dev`

**Permissions**:
- S3 read access to Knowledge Base documents bucket
- Bedrock model invocation (Titan embeddings)
- OpenSearch Serverless access

**Trust Policy**: Bedrock service

### 2. AgentCore Execution Role
**Name**: `faultcast-agentcore-execution-dev`

**Permissions**:
- SSM Parameter Store read (`/faultcast/*`)
- S3 read/write to work schedules bucket
- Bedrock Knowledge Base retrieve
- Bedrock model invocation (Nova Pro)

**Trust Policy**: Bedrock service

## Using Existing Knowledge Base

If you already have a Knowledge Base, set in `terraform.tfvars`:

```hcl
create_knowledge_base = false
knowledge_base_id     = "YOUR_EXISTING_KB_ID"
```

This will:
- Skip Knowledge Base creation
- Use your existing Knowledge Base ID
- Still create AgentCore IAM role with access to your KB

## Updating Knowledge Base Documents

To update documents in the Knowledge Base:

```bash
# Upload new/updated documents
aws s3 cp new_playbook.md s3://$KB_BUCKET/playbooks/

# Trigger sync
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region eu-west-1
```

## Troubleshooting

### Knowledge Base Ingestion Fails

Check IAM permissions:
```bash
aws iam get-role --role-name faultcast-kb-role-dev
aws iam list-role-policies --role-name faultcast-kb-role-dev
```

### Agent Can't Access Knowledge Base

Check AgentCore role permissions:
```bash
aws iam get-role --role-name faultcast-agentcore-execution-dev
aws iam list-role-policies --role-name faultcast-agentcore-execution-dev
```

### OpenSearch Collection Not Ready

Wait for collection to be active:
```bash
aws opensearchserverless list-collections --region eu-west-1
```

## Cleanup

To destroy all resources:

```bash
# Delete agent first
agentcore delete

# Then destroy Terraform resources
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

**Note**: You'll need to confirm deletion of:
- S3 buckets (must be empty)
- OpenSearch collections
- Knowledge Base

## Cost Estimation

Approximate monthly costs (us-east-1 pricing):

- **OpenSearch Serverless**: ~$700/month (4 OCUs)
- **S3 Storage**: ~$0.023/GB
- **Bedrock Knowledge Base**: Pay per query
- **Bedrock Model Invocations**: Pay per token
- **SSM Parameters**: Free (standard parameters)

**Total**: ~$700-1000/month depending on usage

## Next Steps

1. ✅ Deploy infrastructure with Terraform
2. ✅ Upload Knowledge Base documents
3. ✅ Sync Knowledge Base
4. ✅ Deploy AgentCore agent
5. ✅ Test end-to-end workflow
6. Configure IoT Core rules (manual or Terraform)
7. Deploy Lambda functions (manual or Terraform)
8. Set up monitoring and alarms
9. Configure CI/CD pipeline

## Support

- Terraform Issues: Check `terraform/README.md`
- Agent Issues: Check `docs/AGENT_INVOCATION_GUIDE.md`
- AWS Issues: Check CloudWatch Logs

---

**Deployment Status**: Complete infrastructure with Knowledge Base ✅
