# Local values for Knowledge Base module

locals {
  kb_bucket_name = var.existing_s3_bucket_name
  kb_bucket_arn  = var.existing_s3_bucket_arn
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
