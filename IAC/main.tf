provider "aws" {
  region = var.aws_region
}

# locals 
locals {
  env = var.environment == "prod" ? true : false
}

# Module for VPC
module "vpc" {
  source            = "./modules/vpc"
  cidr_block        = var.vpc_cidr
  name              = "RELU-VPC-${var.environment}"
  public_subnet_ids = module.subnets.public_subnet_ids
}

# Module for Subnets
module "subnets" {
  source = "./modules/subnets"
  vpc_id = module.vpc.vpc_id

  public_subnets = [
    { cidr = "192.168.16.0/24", az = "${var.aws_region}a", name = "PublicSubnet1" },
    { cidr = "192.168.32.0/20", az = "${var.aws_region}b", name = "PublicSubnet2" },
    { cidr = "192.168.48.0/20", az = "${var.aws_region}c", name = "PublicSubnet3" }
  ]

  private_subnets = [
    { cidr = "192.168.64.0/20", az = "${var.aws_region}a", name = "PrivateSubnet1" },
    { cidr = "192.168.80.0/20", az = "${var.aws_region}b", name = "PrivateSubnet2" },
    { cidr = "192.168.96.0/20", az = "${var.aws_region}c", name = "PrivateSubnet3" }
  ]
}


module "iam" {
  source = "./modules/iam"

}

# Module for Lambda Function
module "lambda" {
  source = "./modules/lambda"

  primary_region                                     = var.aws_region
  conveyor_motor_simulator_lambda_name               = var.conveyor_motor_simulator_lambda_name
  bedrock_agent_arn                                  = var.bedrock_agent_arn
  conveyor_motor_simulator_lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  bedrock_agent_lambda_execution_role_arn            = module.iam.lambda_execution_role_arn
  app_env_vars                                       = { "environment" = var.environment }
  bedrock_agent_lambda_name                          = var.bedrock_agent_lambda_name
  feature_engineer_lambda_name                       = var.feature_engineer_lambda_name
  feature_engineer_lambda_execution_role_arn         = module.iam.lambda_execution_role_arn
}

# Module for IoT Core
module "iot_core" {
  source = "./modules/iot_core"

  lambda_function_arn = module.lambda.bedrock_agent_lambda_function_arn
}

# Module for EventBridge Rule
module "eventsbridge" {
  source = "./modules/eventsbridge"

  schedule_name = var.schedule_name
  target_arn    = module.lambda.conveyor_motor_simulator_lambda_function_arn
}

module "sagemaker" {
  source = "./modules/sagemaker"

  vpc_id                           = module.vpc.vpc_id
  subnet_id                        = module.subnets.private_subnet_ids
  sagemaker_domain_name            = var.sagemaker_domain_name
  sagemaker_execution_role_arn     = module.iam.sagemaker_execution_role_arn
  sagemaker_distribution_image_arn = var.sagemaker_distribution_image_arn
}

## block to allow S3 to invoke the feature_engineer Lambda function
# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.feature_engineer_lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = data.aws_s3_bucket.conveyor_batch_bucket.arn
}

# Data source to reference the existing conveyor-batch S3 bucket
data "aws_s3_bucket" "conveyor_batch_bucket" {
  bucket = var.conveyor_batch_bucket_name
}

# S3 Event Notification to trigger Lambda
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = data.aws_s3_bucket.conveyor_batch_bucket.id

  lambda_function {
    lambda_function_arn = module.lambda.feature_engineer_lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "conveyor_batches/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}