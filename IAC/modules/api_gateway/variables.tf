variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "relu-pmf-api"
}

variable "environment" {
  description = "The deployment environment (e.g., dev, staging, prod)"
  type        = string
}

variable "stage_name" {
  description = "Stage name for API Gateway deployment"
  type        = string
  default     = "prod"
}

# Lambda function ARNs for integrations
variable "ml_inference_lambda_function_arn" {
  description = "ARN of the ML inference Lambda function"
  type        = string
}

variable "prompt_lambda_function_arn" {
  description = "ARN of the prompt Lambda function"
  type        = string
}

variable "schedules_lambda_function_arn" {
  description = "ARN of the schedules Lambda function"
  type        = string
}

variable "sensor_readings_lambda_function_arn" {
  description = "ARN of the sensor readings Lambda function"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

# Lambda function names for permissions
variable "ml_inference_lambda_function_name" {
  description = "Name of the ML inference Lambda function"
  type        = string
}

variable "prompt_lambda_function_name" {
  description = "Name of the prompt Lambda function"
  type        = string
}

variable "schedules_lambda_function_name" {
  description = "Name of the schedules Lambda function"
  type        = string
}

variable "sensor_readings_lambda_function_name" {
  description = "Name of the sensor readings Lambda function"
  type        = string
}