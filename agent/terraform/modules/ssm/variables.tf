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
