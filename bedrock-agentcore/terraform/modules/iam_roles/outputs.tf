output "agentcore_execution_role_arn" {
  description = "AgentCore execution role ARN"
  value       = aws_iam_role.agentcore_execution.arn
}

output "agentcore_execution_role_name" {
  description = "AgentCore execution role name"
  value       = aws_iam_role.agentcore_execution.name
}

output "knowledge_base_role_arn" {
  description = "Knowledge Base IAM role ARN"
  value       = var.create_knowledge_base ? aws_iam_role.knowledge_base[0].arn : null
}

output "knowledge_base_role_name" {
  description = "Knowledge Base IAM role name"
  value       = var.create_knowledge_base ? aws_iam_role.knowledge_base[0].name : null
}
