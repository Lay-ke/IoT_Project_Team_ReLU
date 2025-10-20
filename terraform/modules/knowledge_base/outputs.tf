output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = aws_cloudformation_stack.knowledge_base.outputs["KnowledgeBaseId"]
}

output "knowledge_base_arn" {
  description = "Bedrock Knowledge Base ARN"
  value       = aws_cloudformation_stack.knowledge_base.outputs["KnowledgeBaseArn"]
}

output "s3_bucket_name" {
  description = "S3 bucket name for Knowledge Base documents"
  value       = local.kb_bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for Knowledge Base documents"
  value       = local.kb_bucket_arn
}

output "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  value       = aws_cloudformation_stack.knowledge_base.outputs["OpenSearchCollectionArn"]
}

output "data_source_ids" {
  description = "Knowledge Base data source IDs"
  value       = [
    aws_cloudformation_stack.knowledge_base.outputs["DataSource1Id"],
    aws_cloudformation_stack.knowledge_base.outputs["DataSource2Id"]
  ]
}

output "data_source_id" {
  description = "Primary Knowledge Base data source ID (first one)"
  value       = aws_cloudformation_stack.knowledge_base.outputs["DataSource1Id"]
}
