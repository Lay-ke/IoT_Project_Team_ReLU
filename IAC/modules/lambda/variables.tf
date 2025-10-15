# AWS Region Configuration
variable "primary_region" {
  description = "Primary AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "lambda_handler_name" {
  description = "Name of the Lambda function handler"
  type        = string
  default     = "lambda_function.lambda_handler"
}

variable "conveyor_motor_simulator_lambda_name" {
  description = "Name of the conveyor motor simulator Lambda function"
  type        = string

}
variable "bedrock_agent_lambda_name" {
  description = "Name of the Bedrock agent Lambda function"
  type        = string

}

variable "conveyor_motor_simulator_lambda_execution_role_arn" {
  description = "ARN of the IAM role assumed by the conveyor motor simulator Lambda function"
  type        = string
}

variable "bedrock_agent_lambda_execution_role_arn" {
  description = "ARN of the IAM role assumed by the Bedrock agent Lambda function"
  type        = string

}

variable "app_env_vars" {
  description = "Environment variables for the Lambda function"
  type        = map(string)
}

variable "bedrock_agent_arn" {
  description = "The ARN of the Bedrock agent that triggers the Lambda function"
  type        = string
}

variable "feature_engineer_lambda_name" {
  description = "Name of the feature engineering Lambda function"
  type        = string

}

variable "feature_engineer_lambda_execution_role_arn" {
  description = "ARN of the IAM role assumed by the feature engineering Lambda function"
  type        = string

}