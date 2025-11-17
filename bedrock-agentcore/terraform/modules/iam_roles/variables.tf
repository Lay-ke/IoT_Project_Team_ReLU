variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "create_knowledge_base" {
  description = "Whether Knowledge Base is being created"
  type        = bool
  default     = false
}
