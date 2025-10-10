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
  name              = "PLight-VPC-${var.environment}"
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

# IAM Role for Lambda Function
# data "aws_iam_policy_document" "lambda_assume_role" {
#   statement {
#     effect = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }
#     actions = ["sts:AssumeRole"]
#   }
# }

# resource "aws_iam_role" "lambda_execution_role" {
#   name               = "lambda-execution-role-${var.environment}"
#   assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
# }

# resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
#   role       = aws_iam_role.lambda_execution_role.name
#   policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
# }

# IAM Role for EventBridge Scheduler
# data "aws_iam_policy_document" "scheduler_assume_role" {
#   statement {
#     effect = "Allow"
#     principals {
#       type        = "Service"
#       identifiers = ["scheduler.amazonaws.com"]
#     }
#     actions = ["sts:AssumeRole"]
#   }
# }

# resource "aws_iam_role" "scheduler_execution_role" {
#   name               = "scheduler-execution-role-${var.environment}"
#   assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
# }

# data "aws_iam_policy_document" "scheduler_lambda_invoke" {
#   statement {
#     effect = "Allow"
#     actions = [
#       "lambda:InvokeFunction"
#     ]
#     resources = ["*"]
#   }
# }

# resource "aws_iam_role_policy" "scheduler_lambda_invoke" {
#   name   = "scheduler-lambda-invoke-${var.environment}"
#   role   = aws_iam_role.scheduler_execution_role.id
#   policy = data.aws_iam_policy_document.scheduler_lambda_invoke.json
# }

module "iam" {
  source = "./modules/iam"
  
}

# Module for Lambda Function
module "lambda" {
  source = "./modules/lambda"
  
  primary_region             = var.aws_region
  conveyor_motor_simulator_lambda_name = var.conveyor_motor_simulator_lambda_name
  bedrock_agent_arn         = var.bedrock_agent_arn
  conveyor_motor_simulator_lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  bedrock_agent_lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  app_env_vars = {"environment" = var.environment}
  bedrock_agent_lambda_name = var.bedrock_agent_lambda_name
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
