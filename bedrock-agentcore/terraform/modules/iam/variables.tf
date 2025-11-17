variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
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

variable "create_knowledge_base" {
  description = "Whether Knowledge Base is being created"
  type        = bool
  default     = false
}

variable "knowledge_base_docs_bucket_arn" {
  description = "S3 bucket ARN for Knowledge Base documents"
  type        = string
  default     = ""
}

variable "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  type        = string
  default     = ""
}
