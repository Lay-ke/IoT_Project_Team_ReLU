output "raw_data_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data_bucket.bucket
}

output "raw_data_bucket_arn" {
  description = "ARN of the raw data S3 bucket"
  value       = aws_s3_bucket.raw_data_bucket.arn
}

output "feature_engineered_data_bucket_name" {
  description = "Name of the feature engineered data S3 bucket"
  value       = aws_s3_bucket.feature_engineered_data_bucket.bucket
}

output "feature_engineered_data_bucket_arn" {
  description = "ARN of the feature engineered data S3 bucket"
  value       = aws_s3_bucket.feature_engineered_data_bucket.arn
}

output "raw_data_bucket_parameter_arn" {
  description = "ARN of the parameter store for raw data bucket name"
  value       = aws_ssm_parameter.raw_data_bucket_name.arn
}

output "feature_engineered_data_bucket_parameter_arn" {
  description = "ARN of the parameter store for feature engineered data bucket name"
  value       = aws_ssm_parameter.feature_engineered_data_bucket_name.arn
}

# Parameter Store names for easy reference
output "bucket_parameter_names" {
  description = "Parameter Store names for all S3 buckets"
  value = {
    raw_data_bucket           = aws_ssm_parameter.raw_data_bucket_name.name
    feature_engineered_bucket = aws_ssm_parameter.feature_engineered_data_bucket_name.name
  }
}