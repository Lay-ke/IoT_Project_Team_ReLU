# Use CloudFormation to create Knowledge Base (better handling of timing issues)
resource "aws_cloudformation_stack" "knowledge_base" {
  name = "${var.project_name}-kb-${var.environment}"

  template_body = file("${path.module}/kb_stack.yaml")

  parameters = {
    ProjectName          = var.project_name
    Environment          = var.environment
    KnowledgeBaseRoleArn = var.knowledge_base_role_arn
    S3BucketArn          = local.kb_bucket_arn
    InclusionPrefixes    = join(",", var.s3_inclusion_prefixes)
  }

  capabilities = ["CAPABILITY_IAM"]

  timeouts {
    create = "30m"
    update = "30m"
    delete = "30m"
  }

  tags = {
    Name        = "${var.project_name}-knowledge-base-stack"
    Environment = var.environment
  }
}
