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

  # Data access Lambda functions
  fetch_ml_inference_data_lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  fetch_raw_sensor_data_lambda_execution_role_arn   = module.iam.lambda_execution_role_arn
  fetch_schedule_data_lambda_execution_role_arn     = module.iam.lambda_execution_role_arn
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

# Module for S3 buckets and related resources
module "s3" {
  source = "./modules/s3"

  raw_data_bucket_name                 = "predictive-maintenance-data-1"
  feature_engineered_data_bucket_name  = "predictive-maintenance-feature-store"
  environment                          = var.environment
  feature_engineer_lambda_function_arn = module.lambda.feature_engineer_lambda_function_arn
  bedrock_agent_lambda_function_arn    = module.lambda.bedrock_agent_lambda_function_arn
}

# Module for API Gateway
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name    = "relu-pmf-api"
  environment = var.environment
  stage_name  = "prod"
  aws_region  = var.aws_region

  # Lambda function ARNs for API Gateway integrations
  ml_inference_lambda_function_arn    = module.lambda.fetch_ml_inference_data_lambda_function_arn
  prompt_lambda_function_arn          = module.lambda.bedrock_agent_lambda_function_arn
  schedules_lambda_function_arn       = module.lambda.fetch_schedule_data_lambda_function_arn
  sensor_readings_lambda_function_arn = module.lambda.fetch_raw_sensor_data_lambda_function_arn

  # Lambda function names for permissions
  ml_inference_lambda_function_name    = module.lambda.fetch_ml_inference_data_lambda_function_name
  prompt_lambda_function_name          = module.lambda.bedrock_agent_lambda_function_name
  schedules_lambda_function_name       = module.lambda.fetch_schedule_data_lambda_function_name
  sensor_readings_lambda_function_name = module.lambda.fetch_raw_sensor_data_lambda_function_name
}

## block to allow S3 to invoke the feature_engineer Lambda function
# Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda.feature_engineer_lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.s3.raw_data_bucket_arn
}

# SSM Parameter for SageMaker Inference Endpoint Name
resource "aws_ssm_parameter" "sagemaker_inference_endpoint_name" {
  name        = "/relu/sagemaker/inference-endpoint-name"
  description = "Name of the SageMaker inference endpoint for PMF model"
  type        = "String"
  value       = "placeholder-endpoint-name"

  tags = {
    Environment = var.environment
    Purpose     = "SageMaker Configuration"
    Project     = "Predictive-Maintenance-Forecaster"
  }
}