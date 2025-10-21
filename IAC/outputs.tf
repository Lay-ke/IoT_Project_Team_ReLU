# S3 Bucket Names
output "conveyor_batch_bucket_name" {
  description = "Name of the conveyor batch processing S3 bucket"
  value       = module.s3.conveyor_batch_bucket_name
}

output "raw_data_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = module.s3.raw_data_bucket_name
}

output "feature_engineered_data_bucket_name" {
  description = "Name of the feature engineered data S3 bucket"
  value       = module.s3.feature_engineered_data_bucket_name
}

# Parameter Store ARNs
output "conveyor_batch_bucket_parameter_arn" {
  description = "ARN of the parameter store for conveyor batch bucket name"
  value       = module.s3.conveyor_batch_bucket_parameter_arn
}

output "raw_data_bucket_parameter_arn" {
  description = "ARN of the parameter store for raw data bucket name"
  value       = module.s3.raw_data_bucket_parameter_arn
}

output "feature_engineered_data_bucket_parameter_arn" {
  description = "ARN of the parameter store for feature engineered data bucket name"
  value       = module.s3.feature_engineered_data_bucket_parameter_arn
}

# Parameter Store Names (for easy reference)
output "bucket_parameter_names" {
  description = "Parameter Store names for all S3 buckets"
  value       = module.s3.bucket_parameter_names
}

# API Gateway Outputs
output "api_gateway_invoke_url" {
  description = "Invoke URL of the API Gateway"
  value       = module.api_gateway.api_gateway_invoke_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_gateway_id
}

output "api_endpoint_urls" {
  description = "Full endpoint URLs for all API paths"
  value       = module.api_gateway.endpoint_urls
}

# SageMaker Inference Endpoint Parameter
output "sagemaker_inference_endpoint_parameter_name" {
  description = "Parameter Store name for SageMaker inference endpoint"
  value       = aws_ssm_parameter.sagemaker_inference_endpoint_name.name
}

output "sagemaker_inference_endpoint_parameter_arn" {
  description = "ARN of the parameter store for SageMaker inference endpoint name"
  value       = aws_ssm_parameter.sagemaker_inference_endpoint_name.arn
}