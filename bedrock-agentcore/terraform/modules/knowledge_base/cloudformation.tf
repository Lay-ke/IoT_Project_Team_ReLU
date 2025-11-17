# Use CloudFormation to create Knowledge Base (better handling of timing issues)
resource "aws_cloudformation_stack" "knowledge_base" {
  name = "${var.project_name}-kb-v2-${var.environment}"

  template_body = file("${path.module}/opensearch_only.yaml")

  parameters = {
    ProjectName          = var.project_name
    Environment          = var.environment
    KnowledgeBaseRoleArn = var.knowledge_base_role_arn
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
