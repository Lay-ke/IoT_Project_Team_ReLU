variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "knowledge_base_role_arn" {
  description = "IAM role ARN for Knowledge Base"
  type        = string
}

variable "s3_inclusion_prefixes" {
  description = "List of S3 prefixes to include in Knowledge Base (e.g., ['inference-data/', 'maintenance-playbooks/'])"
  type        = list(string)
  default     = []
}

variable "use_existing_s3_bucket" {
  description = "Whether to use an existing S3 bucket for Knowledge Base documents"
  type        = bool
  default     = true
}

variable "existing_s3_bucket_name" {
  description = "Name of existing S3 bucket for Knowledge Base documents (required if use_existing_s3_bucket = true)"
  type        = string
  default     = ""
}

variable "existing_s3_bucket_arn" {
  description = "ARN of existing S3 bucket for Knowledge Base documents (required if use_existing_s3_bucket = true)"
  type        = string
  default     = ""
}
