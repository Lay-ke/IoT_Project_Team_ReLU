# FaultCast Terraform Setup Guide

## Repository Cleanup Complete ✅

The repository has been cleaned and organized for Infrastructure as Code (IaC) with Terraform.

## New Structure

```
faultcast/
├── faultcast/                      # Agent source code
│   ├── agents/                     # Agent implementation
│   │   ├── __init__.py
│   │   └── faultcast_maintenance_agent.py
│   └── utils/                      # Utilities
│       ├── __init__.py
│       └── data_simulator.py
├── terraform/                      # Infrastructure as Code
│   ├── main.tf                     # Main configuration
│   ├── variables.tf                # Input variables
│   ├── outputs.tf                  # Output values
│   ├── README.md                   # Terraform documentation
│   ├── modules/                    # Terraform modules
│   │   ├── s3/                     # S3 bucket module
│   │   ├── ssm/                    # SSM parameters module
│   │   ├── agentcore/              # AgentCore IAM module
│   │   ├── iot/                    # IoT Core module (placeholder)
│   │   └── lambda/                 # Lambda functions module (placeholder)
│   └── environments/               # Environment configs
│       ├── dev/                    # Development
│       │   └── terraform.tfvars
│       └── prod/                   # Production (placeholder)
├── docs/                           # Documentation
│   ├── AGENT_INVOCATION_GUIDE.md
│   ├── FAULTCAST_ARCHITECTURE.md
│   ├── QUICK_REFERENCE.md
│   └── DEPLOYMENT_STATUS.md
├── tests/                          # Test files
│   ├── test_local_agent.py
│   ├── test_actual_format.py
│   ├── test_ssm_config.py
│   └── invoke_agent_example.py
├── scripts/                        # Utility scripts
│   ├── deploy_to_agentcore.sh
│   └── aws_setup.py
├── faultcast_agentcore.py          # AgentCore wrapper
├── agentcore-requirements.txt      # Agent dependencies
├── requirements.txt                # Development dependencies
├── .env.example                    # Environment template
├── .dockerignore                   # Docker ignore rules
├── .gitignore                      # Git ignore rules
├── playbook.md                     # Maintenance playbook
├── sample_sensor_data.json         # Sample data
└── README.md                       # Main documentation
```

## What Was Removed

- Duplicate documentation files
- Old deployment guides
- Test log files
- Temporary files
- Unused directories (mcp-server, sdk-python, samples)
- Python cache files
- Virtual environment directory

## What Was Organized

- ✅ Documentation moved to `docs/`
- ✅ Tests moved to `tests/`
- ✅ Scripts moved to `scripts/`
- ✅ Terraform infrastructure created in `terraform/`
- ✅ Clean `.gitignore` created
- ✅ Main README updated

## Terraform Modules Created

### 1. S3 Module (`terraform/modules/s3/`)
- Creates S3 bucket for work schedules
- Enables versioning and encryption
- Configures lifecycle policies
- Blocks public access

### 2. SSM Module (`terraform/modules/ssm/`)
- Creates SSM parameters for configuration
- Stores Knowledge Base ID
- Stores S3 bucket name
- Stores region information

### 3. AgentCore Module (`terraform/modules/agentcore/`)
- Creates IAM execution role
- Configures SSM parameter access
- Configures S3 read/write access
- Configures Bedrock Knowledge Base access
- Configures Bedrock model invocation

### 4. IoT Module (`terraform/modules/iot/`)
- Placeholder for IoT Core rules
- Ready for IoT topic configuration

### 5. Lambda Module (`terraform/modules/lambda/`)
- Placeholder for Lambda functions
- Ready for ML inference Lambda
- Ready for sensor simulation Lambda

## Next Steps

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var-file="environments/dev/terraform.tfvars"
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### 2. Update Configuration

Edit `terraform/environments/dev/terraform.tfvars` with your values:
- Knowledge Base ID
- SageMaker endpoint name
- AgentCore agent ARN

### 3. Deploy Agent

```bash
agentcore configure --entrypoint faultcast_agentcore.py
agentcore launch
```

### 4. Test Deployment

```bash
cd tests
python test_local_agent.py
python invoke_agent_example.py
```

## Terraform Commands

### Initialize
```bash
terraform init
```

### Plan
```bash
terraform plan -var-file="environments/dev/terraform.tfvars"
```

### Apply
```bash
terraform apply -var-file="environments/dev/terraform.tfvars"
```

### Destroy
```bash
terraform destroy -var-file="environments/dev/terraform.tfvars"
```

### Format
```bash
terraform fmt -recursive
```

### Validate
```bash
terraform validate
```

## Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your AWS credentials and configuration.

## Git Workflow

### Initialize Repository
```bash
git init
git add .
git commit -m "Initial commit: Clean repository with Terraform IaC"
```

### Create Remote Repository
```bash
git remote add origin <your-repo-url>
git push -u origin main
```

## CI/CD Integration

The Terraform structure is ready for CI/CD integration with:
- GitHub Actions
- GitLab CI
- AWS CodePipeline
- Jenkins

## Security Best Practices

1. ✅ Never commit `.env` files
2. ✅ Use remote state with S3 backend
3. ✅ Enable state locking with DynamoDB
4. ✅ Use IAM roles instead of access keys
5. ✅ Enable encryption for S3 buckets
6. ✅ Use SSM Parameter Store for secrets
7. ✅ Follow least privilege principle for IAM

## Monitoring

After deployment, monitor:
- CloudWatch Logs: `/aws/bedrock-agentcore/runtimes/relu_agent-*`
- GenAI Observability Dashboard
- S3 bucket for work schedules
- SSM parameters

## Support

- Terraform Documentation: `terraform/README.md`
- Agent Documentation: `docs/AGENT_INVOCATION_GUIDE.md`
- Architecture: `docs/FAULTCAST_ARCHITECTURE.md`

---

**Status**: Repository cleaned and ready for Terraform deployment ✅  
**Date**: October 17, 2025
