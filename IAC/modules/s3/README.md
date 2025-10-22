# S3 Module

This module manages all S3 buckets and related resources for the Predictive Maintenance Forecaster (PMF) project.

## Resources Created

### S3 Buckets
- **Conveyor Batch Bucket** (Data source) - References existing bucket for conveyor batch processing
- **Raw Data Bucket** - Stores raw predictive maintenance data
- **Feature Engineered Data Bucket** - Stores processed features for ML models

### Additional Resources
- **S3 Event Notification** - Triggers Lambda function when new data arrives
- **Parameter Store** - Stores bucket names for easy reference across services

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| raw_data_bucket_name | Name of the S3 bucket for raw predictive maintenance data | `string` | `"predictive-maintenance-data-1"` | no |
| feature_engineered_data_bucket_name | Name of the S3 bucket for feature engineered data | `string` | `"predictive-maintenance-feature-store"` | no |
| environment | The deployment environment (e.g., dev, staging, prod) | `string` | n/a | yes |
| feature_engineer_lambda_function_arn | ARN of the feature engineer Lambda function | `string` | n/a | yes |
| lambda_permission_dependency | Dependency for Lambda permission resource | `any` | `null` | no |

## Outputs

| Name | Description |
|------|-------------|
| raw_data_bucket_name | Name of the raw data S3 bucket |
| raw_data_bucket_arn | ARN of the raw data S3 bucket |
| feature_engineered_data_bucket_name | Name of the feature engineered data S3 bucket |
| feature_engineered_data_bucket_arn | ARN of the feature engineered data S3 bucket |
| bucket_parameter_names | Parameter Store names for all S3 buckets |

## Usage

```hcl
module "s3" {
  source = "./modules/s3"

  raw_data_bucket_name                 = "my-raw-data-bucket"
  feature_engineered_data_bucket_name  = "my-feature-store-bucket"
  environment                          = "production"
  feature_engineer_lambda_function_arn = module.lambda.feature_engineer_lambda_function_arn
}
```

## Parameter Store Integration

The module automatically creates Parameter Store entries for all bucket names:
- `/relu/s3/conveyor-batch-bucket-name`
- `/relu/s3/raw-data-bucket-name`
- `/relu/s3/feature-store-bucket-name`

These can be referenced by Lambda functions and other AWS services for dynamic bucket name resolution.