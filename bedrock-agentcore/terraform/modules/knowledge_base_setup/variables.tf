variable "collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  type        = string
}

variable "kb_role_arn" {
  description = "Knowledge Base IAM role ARN"
  type        = string
}

variable "policy_name" {
  description = "OpenSearch data access policy name"
  type        = string
}

variable "collection_name" {
  description = "OpenSearch collection name"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}
