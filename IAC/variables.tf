variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_cidr" {
  description = "The CIDR block for the VPC"
  type        = string
  default     = "192.168.0.0/16"
}

# Lambda Function Configuration

variable "lambda_handler_name" {
  description = "Handler name for the Lambda function"
  type        = string
  default     = "lambda_function.lambda_handler"
}

variable "lambda_env_vars" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
  default = {
    ENVIRONMENT = "prod"
    LOG_LEVEL   = "INFO"
  }
}

# Conveyor Motor Simulator Lambda Configuration
variable "conveyor_motor_simulator_lambda_name" {
  description = "Name of the conveyor motor simulator Lambda function"
  type        = string
  default     = "conveyor_motor_simulator"
}

variable "bedrock_agent_lambda_name" {
  description = "Name of the Bedrock agent Lambda function"
  type        = string
  default     = "bedrock_agent_query"
}

# Bedrock Configuration
variable "bedrock_agent_arn" {
  description = "ARN of the Bedrock agent"
  type        = string
  default     = ""
}

# EventBridge Scheduler Configuration
variable "schedule_name" {
  description = "Name of the EventBridge Scheduler schedule"
  type        = string
  default     = "agentic-ai-schedule"
}

variable "conveyor_batch_bucket_name" {
  description = "Name of the S3 bucket for conveyor batch processing"
  type        = string
  default     = "predictive-maintenance-models-1"
}

variable "feature_engineer_lambda_name" {
  description = "Name of the feature engineering Lambda function"
  type        = string
  default     = "feature_engineering"
}

variable "sagemaker_domain_name" {
  description = "Name of the SageMaker domain"
  type        = string
  default     = "relu-sagemaker-domain"

}

variable "sagemaker_distribution_image_arn" {
  description = "ARN of the SageMaker distribution image"
  type        = string
  default     = "arn:aws:sagemaker:eu-west-1:<account_id>:image/Sagemaker Distribution 3.4.2"
}