variable "environment" {
  description = "Environment name"
  type        = string
}

variable "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  type        = string
}

variable "work_schedule_bucket" {
  description = "S3 bucket name for work schedules"
  type        = string
}

variable "ssm_parameter_prefix" {
  description = "SSM parameter prefix path (e.g., /faultcast or /myapp)"
  type        = string
  default     = "/faultcast/v2"
}
