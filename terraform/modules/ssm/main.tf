# SSM Parameter Store Module

# AWS Configuration
resource "aws_ssm_parameter" "aws_region" {
  name        = "/faultcast/aws-region"
  description = "FaultCast AWS Region"
  type        = "String"
  value       = data.aws_region.current.name

  tags = {
    Environment = var.environment
  }
}

# Bedrock Configuration
resource "aws_ssm_parameter" "bedrock_region" {
  name        = "/faultcast/bedrock-region"
  description = "FaultCast Bedrock Region"
  type        = "String"
  value       = data.aws_region.current.name

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "bedrock_model_id" {
  name        = "/faultcast/bedrock-model-id"
  description = "FaultCast Bedrock Model ID"
  type        = "String"
  value       = "amazon.nova-pro-v1:0"

  tags = {
    Environment = var.environment
  }
}

# Knowledge Base Configuration
resource "aws_ssm_parameter" "knowledge_base_id" {
  name        = "/faultcast/knowledge-base-id"
  description = "FaultCast Knowledge Base ID"
  type        = "String"
  value       = var.knowledge_base_id
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "knowledge_base_region" {
  name        = "/faultcast/knowledge-base-region"
  description = "FaultCast Knowledge Base Region"
  type        = "String"
  value       = data.aws_region.current.name
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Work Schedule Configuration
resource "aws_ssm_parameter" "work_schedule_bucket" {
  name        = "/faultcast/work-schedule-bucket"
  description = "FaultCast Work Schedule S3 Bucket"
  type        = "String"
  value       = var.work_schedule_bucket
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "work_schedule_prefix" {
  name        = "/faultcast/work-schedule-prefix"
  description = "FaultCast Work Schedule S3 Prefix"
  type        = "String"
  value       = "maintenance-schedules/"
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Application Configuration
resource "aws_ssm_parameter" "environment" {
  name        = "/faultcast/environment"
  description = "FaultCast Environment"
  type        = "String"
  value       = var.environment

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "log_level" {
  name        = "/faultcast/log-level"
  description = "FaultCast Log Level"
  type        = "String"
  value       = "INFO"

  tags = {
    Environment = var.environment
  }
}

data "aws_region" "current" {}
