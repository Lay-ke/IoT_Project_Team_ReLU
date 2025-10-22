output "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  value       = aws_cloudformation_stack.knowledge_base.outputs["CollectionArn"]
}

output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  value       = aws_cloudformation_stack.knowledge_base.outputs["CollectionEndpoint"]
}
