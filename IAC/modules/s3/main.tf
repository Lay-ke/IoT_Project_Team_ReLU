# Raw data bucket for predictive maintenance
resource "aws_s3_bucket" "raw_data_bucket" {
  bucket = var.raw_data_bucket_name

  tags = {
    Name        = "Raw Data Bucket"
    Environment = var.environment
    Purpose     = "Predictive Maintenance Raw Data"
  }
}

# Feature engineered data bucket
resource "aws_s3_bucket" "feature_engineered_data_bucket" {
  bucket = var.feature_engineered_data_bucket_name

  tags = {
    Name        = "Feature Engineered Data Bucket"
    Environment = var.environment
    Purpose     = "Predictive Maintenance Feature Store"
  }
}

# S3 Event Notification to trigger Lambda
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.raw_data_bucket.id

  lambda_function {
    lambda_function_arn = var.feature_engineer_lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "conveyor_batches/"
    filter_suffix       = ".json"
  }
}

# AWS Systems Manager Parameter Store for S3 bucket names
resource "aws_ssm_parameter" "raw_data_bucket_name" {
  name        = "/relu/s3/raw-data-bucket-name"
  description = "Name of the S3 bucket for raw predictive maintenance data"
  type        = "String"
  value       = aws_s3_bucket.raw_data_bucket.bucket

  tags = {
    Environment = var.environment
    Purpose     = "S3 Bucket Configuration"
  }
}

resource "aws_ssm_parameter" "feature_engineered_data_bucket_name" {
  name        = "/relu/s3/feature-store-bucket-name"
  description = "Name of the S3 bucket for feature engineered data"
  type        = "String"
  value       = aws_s3_bucket.feature_engineered_data_bucket.bucket

  tags = {
    Environment = var.environment
    Purpose     = "S3 Bucket Configuration"
  }
}