# IAM Module - All IAM Roles and Policies for FaultCast

# ============================================================================
# AgentCore Execution Role
# ============================================================================

resource "aws_iam_role" "agentcore_execution" {
  name = "${var.project_name}-agentcore-execution-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-agentcore-execution"
    Environment = var.environment
  }
}

# SSM Parameter Access Policy for AgentCore
resource "aws_iam_role_policy" "agentcore_ssm_access" {
  name = "ssm-parameter-access"
  role = aws_iam_role.agentcore_execution.id

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
  role = aws_iam_role.agentcore_execution.id

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
  role = aws_iam_role.agentcore_execution.id

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
  role = aws_iam_role.agentcore_execution.id

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
  role = aws_iam_role.agentcore_execution.id

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

# ============================================================================
# Knowledge Base Role
# ============================================================================

resource "aws_iam_role" "knowledge_base" {
  count = var.create_knowledge_base ? 1 : 0
  name  = "${var.project_name}-kb-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-knowledge-base-role"
    Environment = var.environment
  }
}

# S3 Access Policy for Knowledge Base
resource "aws_iam_role_policy" "knowledge_base_s3" {
  count = var.create_knowledge_base ? 1 : 0
  name  = "s3-access"
  role  = aws_iam_role.knowledge_base[0].id

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
  role  = aws_iam_role.knowledge_base[0].id

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
  role  = aws_iam_role.knowledge_base[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn
      }
    ]
  })
}



data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# SES Access for Email Notifications
resource "aws_iam_role_policy" "agentcore_ses_access" {
  name = "ses-email-access"
  role = aws_iam_role.agentcore_execution.id

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

