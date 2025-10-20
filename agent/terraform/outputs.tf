# FaultCast Terraform Outputs

output "work_schedule_bucket_name" {
  description = "S3 bucket name for work schedules"
  value       = var.existing_kb_s3_bucket_name
}

output "work_schedule_bucket_arn" {
  description = "S3 bucket ARN for work schedules"
  value       = var.existing_kb_s3_bucket_arn
}

# IoT and Lambda outputs - Disabled for now
# output "iot_topic_rule_name" {
#   description = "IoT topic rule name"
#   value       = module.iot.topic_rule_name
# }

# output "ml_inference_lambda_arn" {
#   description = "ML inference Lambda function ARN"
#   value       = module.lambda.ml_inference_lambda_arn
# }

output "agentcore_execution_role_arn" {
  description = "AgentCore execution role ARN"
  value       = module.iam_roles.agentcore_execution_role_arn
}

output "agentcore_execution_role_name" {
  description = "AgentCore execution role name"
  value       = module.iam_roles.agentcore_execution_role_name
}

output "knowledge_base_role_arn" {
  description = "Knowledge Base IAM role ARN"
  value       = module.iam_roles.knowledge_base_role_arn
}



output "ssm_parameter_paths" {
  description = "SSM parameter paths"
  value       = module.ssm.parameter_paths
}

output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = var.create_knowledge_base ? module.knowledge_base[0].knowledge_base_id : var.knowledge_base_id
}

output "knowledge_base_arn" {
  description = "Bedrock Knowledge Base ARN"
  value       = var.create_knowledge_base ? module.knowledge_base[0].knowledge_base_arn : null
}

output "knowledge_base_s3_bucket" {
  description = "S3 bucket for Knowledge Base documents"
  value       = var.create_knowledge_base ? module.knowledge_base[0].s3_bucket_name : var.existing_kb_s3_bucket_name
}

output "knowledge_base_data_source_ids" {
  description = "Knowledge Base data source IDs"
  value       = var.create_knowledge_base ? module.knowledge_base[0].data_source_ids : null
}
