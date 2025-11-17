# IAM Policies Module - Attach policies to existing roles

# SSM Parameter Access Policy for AgentCore
resource "aws_iam_role_policy" "agentcore_ssm_access" {
  name = "ssm-parameter-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/faultcast/*"
      }
    ]
  })
}

# S3 Access Policy for AgentCore
resource "aws_iam_role_policy" "agentcore_s3_access" {
  name = "s3-work-schedule-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::${var.work_schedule_bucket}/maintenance-schedules/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.work_schedule_bucket}"
      }
    ]
  })
}

# Bedrock Knowledge Base Access Policy for AgentCore
resource "aws_iam_role_policy" "agentcore_knowledge_base_access" {
  name = "bedrock-knowledge-base-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:knowledge-base/${var.knowledge_base_id}"
      }
    ]
  })
}

# Bedrock Model Access Policy for AgentCore
resource "aws_iam_role_policy" "agentcore_bedrock_model_access" {
  name = "bedrock-model-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.nova-pro-v1:0",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.nova-lite-v1:0"
        ]
      }
    ]
  })
}

# CloudWatch Logs Access for AgentCore
resource "aws_iam_role_policy" "agentcore_cloudwatch_logs" {
  name = "cloudwatch-logs-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/*"
      }
    ]
  })
}

# SES Access for Email Notifications
resource "aws_iam_role_policy" "agentcore_ses_access" {
  name = "ses-email-access"
  role = var.agentcore_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# S3 Access Policy for Knowledge Base
resource "aws_iam_role_policy" "knowledge_base_s3" {
  count = var.create_knowledge_base ? 1 : 0
  name  = "s3-access"
  role  = var.knowledge_base_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.knowledge_base_docs_bucket_arn,
          "${var.knowledge_base_docs_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Bedrock Model Access Policy for Knowledge Base (Embeddings)
resource "aws_iam_role_policy" "knowledge_base_bedrock" {
  count = var.create_knowledge_base ? 1 : 0
  name  = "bedrock-model-access"
  role  = var.knowledge_base_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v1",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/amazon.titan-embed-text-v2:0"
        ]
      }
    ]
  })
}

# OpenSearch Serverless Access for Knowledge Base
resource "aws_iam_role_policy" "knowledge_base_opensearch" {
  count = var.create_knowledge_base ? 1 : 0
  name  = "opensearch-serverless-access"
  role  = var.knowledge_base_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn != "" ? var.opensearch_collection_arn : "*"
      }
    ]
  })
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
