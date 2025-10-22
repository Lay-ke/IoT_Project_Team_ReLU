variable "raw_data_bucket_name" {
  description = "Name of the S3 bucket for raw predictive maintenance data"
  type        = string
  default     = "predictive-maintenance-data-1"
}

variable "feature_engineered_data_bucket_name" {
  description = "Name of the S3 bucket for feature engineered data"
  type        = string
  default     = "predictive-maintenance-feature-store"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "feature_engineer_lambda_function_arn" {
  description = "ARN of the feature engineer Lambda function"
  type        = string
}

variable "bedrock_agent_lambda_function_arn" {
  description = "ARN of the Bedrock agent Lambda function"
  type        = string

}