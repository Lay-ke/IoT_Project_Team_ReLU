# FaultCast Terraform Variables

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "faultcast"
}

variable "create_knowledge_base" {
  description = "Whether to create a new Knowledge Base or use existing"
  type        = bool
  default     = true
}

variable "knowledge_base_id" {
  description = "AWS Bedrock Knowledge Base ID (required if create_knowledge_base = false)"
  type        = string
  default     = ""
}

variable "use_existing_kb_s3_bucket" {
  description = "Whether to use an existing S3 bucket for Knowledge Base documents"
  type        = bool
  default     = false
}

variable "existing_kb_s3_bucket_name" {
  description = "Name of existing S3 bucket for Knowledge Base documents (required if use_existing_kb_s3_bucket = true)"
  type        = string
  default     = ""
}

variable "existing_kb_s3_bucket_arn" {
  description = "ARN of existing S3 bucket for Knowledge Base documents (required if use_existing_kb_s3_bucket = true)"
  type        = string
  default     = ""
}

variable "kb_s3_inclusion_prefixes" {
  description = "List of S3 prefixes to include in Knowledge Base (e.g., ['inference-data/', 'maintenance-playbooks/'])"
  type        = list(string)
  default     = []
}

variable "sagemaker_endpoint_name" {
  description = "SageMaker endpoint name for ML inference"
  type        = string
}

variable "agentcore_agent_arn" {
  description = "AWS Bedrock AgentCore agent ARN"
  type        = string
  default     = ""
}

variable "enable_monitoring" {
  description = "Enable CloudWatch monitoring and alarms"
  type        = bool
  default     = true
}

variable "sensor_simulation_schedule" {
  description = "EventBridge schedule expression for sensor simulation"
  type        = string
  default     = "rate(1 minute)"
}
