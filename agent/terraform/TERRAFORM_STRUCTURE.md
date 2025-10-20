# FaultCast Terraform Module Structure

## Module Architecture

```
terraform/
├── main.tf                          # Root module - orchestrates all modules
├── variables.tf                     # Input variables
├── outputs.tf                       # Output values
├── README.md                        # Documentation
├── DEPLOYMENT_GUIDE.md              # Step-by-step deployment
│
├── modules/
│   ├── iam/                         # IAM Module (Centralized)
│   │   ├── main.tf                  # All IAM roles and policies
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │   
│   │   Creates:
│   │   • AgentCore Execution Role
│   │   • Knowledge Base Role
│   │   • Lambda Execution Role (optional)
│   │   • All associated policies
│   │
│   ├── knowledge_base/              # Knowledge Base Module
│   │   ├── main.tf                  # KB, OpenSearch, S3, Data Source
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │   
│   │   Creates:
│   │   • Bedrock Knowledge Base
│   │   • OpenSearch Serverless Collection
│   │   • S3 bucket for KB documents
│   │   • Data source configuration
│   │   • Security policies
│   │
│   ├── s3/                          # S3 Module
│   │   ├── main.tf                  # Work schedule bucket
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │   
│   │   Creates:
│   │   • S3 bucket for work schedules
│   │   • Versioning, encryption
│   │   • Lifecycle policies
│   │
│   ├── ssm/                         # SSM Module
│   │   ├── main.tf                  # Configuration parameters
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │   
│   │   Creates:
│   │   • /faultcast/knowledge-base-id
│   │   • /faultcast/knowledge-base-region
│   │   • /faultcast/work-schedule-bucket
│   │   • /faultcast/work-schedule-prefix
│   │
│   ├── iot/                         # IoT Module (Placeholder)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── lambda/                      # Lambda Module (Placeholder)
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
└── environments/
    ├── dev/
    │   └── terraform.tfvars         # Dev environment config
    └── prod/
        └── terraform.tfvars         # Prod environment config (placeholder)
```

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                         Root Module                         │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  S3 Module   │    │  IAM Module  │    │ KB Module    │
│              │    │              │    │ (conditional)│
│  • Work      │    │  • AgentCore │    │              │
│    Schedules │    │    Role      │    │  • Bedrock   │
│    Bucket    │    │  • KB Role   │    │    KB        │
│              │    │  • Lambda    │    │  • OpenSearch│
│              │    │    Role      │    │  • S3 Docs   │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  SSM Module  │
                    │              │
                    │  • Config    │
                    │    Parameters│
                    └──────────────┘
```

## IAM Module Details

### AgentCore Execution Role

**Role Name**: `faultcast-agentcore-execution-{environment}`

**Policies**:
1. **SSM Parameter Access**
   - `ssm:GetParameter`
   - `ssm:GetParameters`
   - `ssm:GetParametersByPath`
   - Resource: `arn:aws:ssm:*:*:parameter/faultcast/*`

2. **S3 Work Schedule Access**
   - `s3:PutObject`, `s3:PutObjectAcl`, `s3:GetObject`
   - `s3:ListBucket`
   - Resource: Work schedules bucket

3. **Bedrock Knowledge Base Access**
   - `bedrock:Retrieve`
   - `bedrock:RetrieveAndGenerate`
   - Resource: FaultCast Knowledge Base

4. **Bedrock Model Access**
   - `bedrock:InvokeModel`
   - `bedrock:InvokeModelWithResponseStream`
   - Resource: Amazon Nova Pro model

5. **CloudWatch Logs Access**
   - `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`
   - Resource: `/aws/bedrock-agentcore/*`

### Knowledge Base Role

**Role Name**: `faultcast-kb-role-{environment}`

**Policies**:
1. **S3 Document Access**
   - `s3:GetObject`, `s3:ListBucket`
   - Resource: KB documents bucket

2. **Bedrock Embeddings Access**
   - `bedrock:InvokeModel`
   - Resource: Titan Embed models

3. **OpenSearch Serverless Access**
   - `aoss:APIAccessAll`
   - Resource: OpenSearch collection

### Lambda Execution Role (Optional)

**Role Name**: `faultcast-lambda-execution-{environment}`

**Policies**:
1. **Basic Lambda Execution** (AWS managed policy)
2. **SageMaker Access**
   - `sagemaker:InvokeEndpoint`
3. **AgentCore Invocation**
   - `bedrock:InvokeAgent`
4. **IoT Publish**
   - `iot:Publish`

## Knowledge Base Module Details

### Components Created

1. **Bedrock Knowledge Base**
   - Vector database for semantic search
   - Embedding model: Titan Embed Text v2
   - Storage: OpenSearch Serverless

2. **OpenSearch Serverless Collection**
   - Type: VECTORSEARCH
   - Index: faultcast-index
   - Fields: vector, text, metadata

3. **S3 Bucket for Documents**
   - Stores maintenance playbooks
   - Stores prediction history
   - Versioning and encryption enabled

4. **Data Source**
   - S3 data source
   - Chunking: Fixed size (300 tokens, 20% overlap)
   - Auto-sync on document upload

5. **Security Policies**
   - Encryption policy (AWS owned key)
   - Network policy (public access)
   - Data access policy (KB role permissions)

## Configuration Options

### Create New Knowledge Base

```hcl
create_knowledge_base = true
```

This will create:
- Complete Knowledge Base infrastructure
- OpenSearch Serverless collection
- S3 bucket for documents
- IAM role with all permissions

### Use Existing Knowledge Base

```hcl
create_knowledge_base = false
knowledge_base_id     = "YOUR_EXISTING_KB_ID"
```

This will:
- Skip Knowledge Base creation
- Use your existing KB ID
- Still create AgentCore IAM role with KB access

## Deployment Order

Terraform handles dependencies automatically, but the logical order is:

1. **S3 Module** - Creates work schedules bucket
2. **IAM Module** - Creates all IAM roles
3. **Knowledge Base Module** - Creates KB infrastructure (uses IAM role)
4. **SSM Module** - Creates configuration parameters (uses KB ID and S3 bucket)

## Post-Deployment Steps

### 1. Upload Knowledge Base Documents

```bash
KB_BUCKET=$(terraform output -raw knowledge_base_s3_bucket)
aws s3 cp playbook.md s3://$KB_BUCKET/playbooks/
```

### 2. Sync Knowledge Base

```bash
KB_ID=$(terraform output -raw knowledge_base_id)
DS_ID=$(terraform output -raw knowledge_base_data_source_id)

aws bedrock-agent start-ingestion-job \
  --knowledge-base-id $KB_ID \
  --data-source-id $DS_ID \
  --region eu-west-1
```

### 3. Deploy AgentCore Agent

```bash
# Get the execution role ARN
ROLE_ARN=$(terraform output -raw agentcore_execution_role_arn)

# Configure and deploy
agentcore configure --entrypoint faultcast_agentcore.py
# Use $ROLE_ARN when prompted for execution role
agentcore launch
```

### 4. Test Complete System

```bash
agentcore invoke '{
  "machine_id": "conveyor-A001",
  "prediction": {
    "predicted_class": "pulley",
    "confidence": 0.961
  }
}'
```

## Resource Naming Convention

All resources follow the pattern: `{project_name}-{resource}-{environment}`

Examples:
- `faultcast-agentcore-execution-dev`
- `faultcast-kb-role-dev`
- `faultcast-kb-docs-dev`
- `faultcast-work-schedules-dev`

## Tags

All resources are tagged with:
- `Project`: FaultCast
- `Environment`: dev/prod
- `ManagedBy`: Terraform

## Security Best Practices

1. ✅ Least privilege IAM policies
2. ✅ S3 buckets encrypted at rest
3. ✅ S3 public access blocked
4. ✅ OpenSearch encryption enabled
5. ✅ IAM roles with service-specific trust policies
6. ✅ Resource-specific permissions (no wildcards)
7. ✅ SSM parameters for sensitive config

## Cost Optimization

- OpenSearch Serverless: Use minimum OCUs
- S3 Lifecycle policies: Archive old schedules
- Knowledge Base: Optimize chunk size
- Lambda: Use appropriate memory settings

---

**Complete Infrastructure**: IAM + Knowledge Base + S3 + SSM ✅
