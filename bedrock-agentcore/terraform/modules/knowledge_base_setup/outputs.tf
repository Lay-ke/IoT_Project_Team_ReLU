output "setup_complete" {
  description = "Knowledge Base setup completion status"
  value       = null_resource.create_knowledge_base.id
}
