# SSM Parameter Store Module

# AWS Configuration
resource "aws_ssm_parameter" "aws_region" {
  name        = "${var.ssm_parameter_prefix}/aws-region"
  description = "FaultCast AWS Region"
  type        = "SecureString"
  value       = data.aws_region.current.name
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Bedrock Configuration
resource "aws_ssm_parameter" "bedrock_region" {
  name        = "${var.ssm_parameter_prefix}/bedrock-region"
  description = "FaultCast Bedrock Region"
  type        = "SecureString"
  value       = data.aws_region.current.name
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "bedrock_model_id" {
  name        = "${var.ssm_parameter_prefix}/bedrock-model-id"
  description = "FaultCast Bedrock Model ID"
  type        = "SecureString"
  value       = "amazon.nova-pro-v1:0"
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Knowledge Base Configuration
resource "aws_ssm_parameter" "knowledge_base_id" {
  name        = "${var.ssm_parameter_prefix}/knowledge-base-id"
  description = "FaultCast Knowledge Base ID"
  type        = "SecureString"
  value       = var.knowledge_base_id
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "knowledge_base_region" {
  name        = "${var.ssm_parameter_prefix}/knowledge-base-region"
  description = "FaultCast Knowledge Base Region"
  type        = "SecureString"
  value       = data.aws_region.current.name
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Work Schedule Configuration
resource "aws_ssm_parameter" "work_schedule_bucket" {
  name        = "${var.ssm_parameter_prefix}/work-schedule-bucket"
  description = "FaultCast Work Schedule S3 Bucket"
  type        = "SecureString"
  value       = var.work_schedule_bucket
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "work_schedule_prefix" {
  name        = "${var.ssm_parameter_prefix}/work-schedule-prefix"
  description = "FaultCast Work Schedule S3 Prefix"
  type        = "SecureString"
  value       = "maintenance-schedules/"
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

# Application Configuration
resource "aws_ssm_parameter" "environment" {
  name        = "${var.ssm_parameter_prefix}/environment"
  description = "FaultCast Environment"
  type        = "SecureString"
  value       = var.environment
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

resource "aws_ssm_parameter" "log_level" {
  name        = "${var.ssm_parameter_prefix}/log-level"
  description = "FaultCast Log Level"
  type        = "SecureString"
  value       = "INFO"
  overwrite   = true

  tags = {
    Environment = var.environment
  }
}

data "aws_region" "current" {}
