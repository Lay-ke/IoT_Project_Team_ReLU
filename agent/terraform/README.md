# FaultCast Terraform Infrastructure

This directory contains the Infrastructure as Code (IaC) for the FaultCast Predictive Maintenance System using Terraform.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS Account with permissions for:
  - S3
  - IAM
  - SSM Parameter Store
  - AWS Bedrock
  - IoT Core
  - Lambda
  - SageMaker

## Project Structure

```
terraform/
├── main.tf                 # Main Terraform configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── modules/
│   ├── s3/                 # S3 bucket for work schedules
│   ├── ssm/                # SSM Parameter Store configuration
│   ├── agentcore/          # AgentCore IAM roles and policies
│   ├── iot/                # IoT Core rules (placeholder)
│   └── lambda/             # Lambda functions (placeholder)
└── environments/
    ├── dev/                # Development environment
    └── prod/               # Production environment
```

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Configure Variables

Edit `environments/dev/terraform.tfvars` with your values:

```hcl
knowledge_base_id       = "YOUR_KB_ID"
sagemaker_endpoint_name = "YOUR_SAGEMAKER_ENDPOINT"
agentcore_agent_arn     = "YOUR_AGENT_ARN"
```

### 3. Plan Deployment

```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

### 4. Apply Configuration

```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

## Modules

### Knowledge Base Module
Creates complete Bedrock Knowledge Base infrastructure:
- Bedrock Knowledge Base (vector database)
- OpenSearch Serverless Collection (vector search)
- S3 bucket for Knowledge Base documents
- IAM role with permissions for S3, Bedrock, OpenSearch
- Data source configuration
- Security policies (encryption, network, data access)

### S3 Module
Creates and configures S3 bucket for work schedule storage with:
- Versioning enabled
- Server-side encryption
- Public access blocked
- Lifecycle policies (90 days → Glacier, 365 days → Delete)

### SSM Module
Creates SSM parameters for runtime configuration:
- `/faultcast/knowledge-base-id`
- `/faultcast/knowledge-base-region`
- `/faultcast/work-schedule-bucket`
- `/faultcast/work-schedule-prefix`

### AgentCore Module
Creates IAM roles and policies for AgentCore:
- Execution role
- SSM parameter access
- S3 read/write access
- Bedrock Knowledge Base access (retrieve)
- Bedrock model invocation (Nova Pro)

### IoT Module (Placeholder)
Will configure:
- IoT topic rules
- IoT rule actions
- Lambda triggers

### Lambda Module (Placeholder)
Will configure:
- ML inference Lambda
- Sensor simulation Lambda
- IAM roles and policies

## Outputs

After applying, Terraform will output:

- `knowledge_base_id` - Bedrock Knowledge Base ID
- `knowledge_base_arn` - Bedrock Knowledge Base ARN
- `knowledge_base_s3_bucket` - S3 bucket for KB documents
- `knowledge_base_data_source_id` - KB data source ID
- `work_schedule_bucket_name` - S3 bucket for work schedules
- `agentcore_execution_role_arn` - IAM role ARN for AgentCore
- `ssm_parameter_paths` - SSM parameter paths

## Remote State (Optional)

To use remote state with S3 backend, uncomment the backend configuration in `main.tf`:

```hcl
backend "s3" {
  bucket         = "faultcast-terraform-state"
  key            = "faultcast/terraform.tfstate"
  region         = "eu-west-1"
  encrypt        = true
  dynamodb_table = "faultcast-terraform-locks"
}
```

Then create the S3 bucket and DynamoDB table:

```bash
aws s3 mb s3://faultcast-terraform-state --region eu-west-1
aws dynamodb create-table \
  --table-name faultcast-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-1
```

## Cleanup

To destroy all resources:

```bash
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

## Next Steps

1. Deploy AgentCore agent using `agentcore` CLI
2. Configure IoT Core rules
3. Deploy Lambda functions
4. Set up SageMaker endpoints
5. Configure monitoring and alarms

## Notes

- The AgentCore agent itself is deployed using the `agentcore` CLI, not Terraform
- This Terraform configuration manages the supporting infrastructure
- Ensure proper AWS credentials and permissions before deployment
