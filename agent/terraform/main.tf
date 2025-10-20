# FaultCast Predictive Maintenance System - Main Terraform Configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.9"
    }
  }

  # Remote state in S3 (using existing bucket)
  backend "s3" {
    bucket  = "predictive-maintenance-feature-store"
    key     = "terraform/terraform.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FaultCast"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# S3 Module - Using existing bucket, no new bucket needed
# module "s3" {
#   source = "./modules/s3"
#   
#   environment  = var.environment
#   project_name = var.project_name
# }

# IAM Roles Module - Create roles first (no policies yet)
module "iam_roles" {
  source = "./modules/iam_roles"

  environment           = var.environment
  project_name          = var.project_name
  create_knowledge_base = var.create_knowledge_base
}

# IAM Policies Module - Attach KB policies with wildcard first
module "iam_policies_kb_initial" {
  count  = var.create_knowledge_base ? 1 : 0
  source = "./modules/iam_policies"

  environment                    = var.environment
  project_name                   = var.project_name
  agentcore_role_name            = module.iam_roles.agentcore_execution_role_name
  knowledge_base_role_name       = module.iam_roles.knowledge_base_role_name
  knowledge_base_id              = "placeholder"  # Will be updated later
  work_schedule_bucket           = var.existing_kb_s3_bucket_name
  create_knowledge_base          = var.create_knowledge_base
  knowledge_base_docs_bucket_arn = var.existing_kb_s3_bucket_arn
  opensearch_collection_arn      = ""  # Wildcard will be used

  depends_on = [module.iam_roles]
}

# Knowledge Base Module (conditional) - Create after IAM policies are attached
module "knowledge_base" {
  count  = var.create_knowledge_base ? 1 : 0
  source = "./modules/knowledge_base"

  environment             = var.environment
  project_name            = var.project_name
  knowledge_base_role_arn = module.iam_roles.knowledge_base_role_arn

  # S3 Bucket Configuration
  use_existing_s3_bucket  = var.use_existing_kb_s3_bucket
  existing_s3_bucket_name = var.existing_kb_s3_bucket_name
  existing_s3_bucket_arn  = var.existing_kb_s3_bucket_arn

  # S3 Prefixes to include in Knowledge Base
  s3_inclusion_prefixes = var.kb_s3_inclusion_prefixes

  depends_on = [module.iam_policies_kb_initial]
}

# IAM Policies Module - Attach AgentCore policies after KB is created
module "iam_policies" {
  source = "./modules/iam_policies"

  environment                    = var.environment
  project_name                   = var.project_name
  agentcore_role_name            = module.iam_roles.agentcore_execution_role_name
  knowledge_base_role_name       = module.iam_roles.knowledge_base_role_name
  knowledge_base_id              = var.create_knowledge_base ? module.knowledge_base[0].knowledge_base_id : var.knowledge_base_id
  work_schedule_bucket           = var.existing_kb_s3_bucket_name
  create_knowledge_base          = false  # Don't recreate KB policies
  knowledge_base_docs_bucket_arn = var.existing_kb_s3_bucket_arn
  opensearch_collection_arn      = ""

  depends_on = [module.knowledge_base]
}

# SSM Parameters Module
module "ssm" {
  source = "./modules/ssm"

  environment          = var.environment
  knowledge_base_id    = var.create_knowledge_base ? module.knowledge_base[0].knowledge_base_id : var.knowledge_base_id
  work_schedule_bucket = var.existing_kb_s3_bucket_name

  depends_on = [module.knowledge_base, module.iam_policies]
}

# IoT Module (placeholder) - Disabled for now
# module "iot" {
#   source = "./modules/iot"
#   
#   environment         = var.environment
#   project_name        = var.project_name
#   lambda_function_arn = module.lambda.ml_inference_lambda_arn
# }

# Lambda Module (placeholder) - Disabled for now
# module "lambda" {
#   source = "./modules/lambda"
#   
#   environment             = var.environment
#   project_name            = var.project_name
#   sagemaker_endpoint_name = var.sagemaker_endpoint_name
#   agentcore_agent_arn     = var.agentcore_agent_arn
# }
