# AgentCore Configuration

## Overview

The FaultCast agent uses a **dynamic configuration** approach where the `.bedrock_agentcore.yaml` file is generated from a template using Terraform outputs.

## Files

### `.bedrock_agentcore.yaml.template`
Template file with placeholders for dynamic values. **This file is committed to git**.

Placeholders:
- `{{AGENT_ENTRYPOINT}}` - Path to agent entrypoint script
- `{{SOURCE_PATH}}` - Agent source directory
- `{{EXECUTION_ROLE_ARN}}` - IAM role ARN from Terraform
- `{{AWS_ACCOUNT_ID}}` - AWS account ID
- `{{AWS_REGION}}` - AWS region
- `{{ECR_REPOSITORY}}` - ECR repository URL

### `.bedrock_agentcore.yaml`
Generated configuration file used by `agentcore launch`. **This file is NOT committed to git** (in .gitignore).

Generated automatically by `terraform/scripts/deploy.sh` using Terraform outputs.

### `.bedrock_agentcore.yaml.backup`
Backup of previous configuration (if exists). **This file is NOT committed to git**.

## How It Works

### During Deployment

1. **Terraform creates infrastructure** including IAM roles
2. **Deploy script retrieves Terraform outputs**:
   - AgentCore execution role ARN
   - AWS region
   - AWS account ID
3. **Script generates config from template**:
   ```bash
   sed -e "s|{{EXECUTION_ROLE_ARN}}|$AGENTCORE_ROLE_ARN|g" \
       .bedrock_agentcore.yaml.template > .bedrock_agentcore.yaml
   ```
4. **agentcore launch uses the generated config**

### Configuration Flow

```
Terraform Apply
    ↓
Creates IAM Role: faultcast-agentcore-exec-v2-dev
    ↓
Deploy Script reads Terraform outputs
    ↓
Generates .bedrock_agentcore.yaml from template
    ↓
agentcore launch uses generated config
    ↓
Agent deployed with Terraform-managed role
```

## Manual Configuration

If you need to manually generate the config:

```bash
cd agent

# Get values from Terraform
cd terraform
AGENTCORE_ROLE_ARN=$(terraform output -raw agentcore_execution_role_arn)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="eu-west-1"
cd ..

# Generate config
AGENT_DIR=$(pwd)
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/bedrock-agentcore-relu_agent"

sed -e "s|{{AGENT_ENTRYPOINT}}|$AGENT_DIR/faultcast_agentcore.py|g" \
    -e "s|{{SOURCE_PATH}}|$AGENT_DIR|g" \
    -e "s|{{EXECUTION_ROLE_ARN}}|$AGENTCORE_ROLE_ARN|g" \
    -e "s|{{AWS_ACCOUNT_ID}}|$AWS_ACCOUNT_ID|g" \
    -e "s|{{AWS_REGION}}|$AWS_REGION|g" \
    -e "s|{{ECR_REPOSITORY}}|$ECR_REPOSITORY|g" \
    .bedrock_agentcore.yaml.template > .bedrock_agentcore.yaml

# Deploy
agentcore launch
```

## Benefits of Dynamic Configuration

1. **Infrastructure as Code** - Config uses Terraform-managed resources
2. **Team Consistency** - Everyone uses the same IAM roles
3. **No Hardcoded Values** - ARNs and IDs are generated dynamically
4. **Easy Updates** - Change Terraform, redeploy, config updates automatically
5. **Version Control** - Template is tracked, generated config is not

## Troubleshooting

### Config not generated

**Problem:** `.bedrock_agentcore.yaml` doesn't exist after deployment

**Solution:**
```bash
# Check if template exists
ls -la agent/.bedrock_agentcore.yaml.template

# Manually generate
cd agent/terraform/scripts
bash deploy.sh
```

### Wrong execution role

**Problem:** Agent uses old/wrong IAM role

**Solution:**
```bash
# Delete old config
rm agent/.bedrock_agentcore.yaml

# Regenerate from template
cd agent/terraform/scripts
bash deploy.sh
```

### Template placeholders not replaced

**Problem:** Config contains `{{PLACEHOLDER}}` values

**Solution:**
```bash
# Check Terraform outputs
cd agent/terraform
terraform output

# Ensure deploy script has access to outputs
terraform output -raw agentcore_execution_role_arn
```

## SSM Parameters

The deployment also saves key values to SSM Parameter Store for programmatic access:

- `/faultcast/v2/knowledge-base-id` - Knowledge Base ID
- `/faultcast/v2/agentcore-role-arn` - AgentCore execution role ARN
- `/faultcast/v2/agent-arn` - Deployed agent ARN (after deployment)

Retrieve with:
```bash
aws ssm get-parameter --name /faultcast/v2/agentcore-role-arn --query Parameter.Value --output text
```

## Notes

- The template uses `null` values for fields that are populated by AgentCore during first launch
- `execution_role_auto_create: false` ensures we use the Terraform-created role
- `ecr_auto_create: false` ensures we use the specified ECR repository
- Memory configuration is preserved from template (STM_AND_LTM mode)
- Observability is enabled by default
