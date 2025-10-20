# Development Environment Configuration

aws_region   = "eu-west-1"
environment  = "dev"
project_name = "faultcast"

# Knowledge Base Configuration
create_knowledge_base = true

# Use existing S3 bucket for Knowledge Base documents
use_existing_kb_s3_bucket   = true
existing_kb_s3_bucket_name  = "predictive-maintenance-feature-store"
existing_kb_s3_bucket_arn   = "arn:aws:s3:::predictive-maintenance-feature-store"

# Only index specific directories (exclude other unrelated data)
kb_s3_inclusion_prefixes = [
  "knowledge-base-inference/",
  "maintenance-schedules/"
]

# SageMaker and AgentCore Configuration
sagemaker_endpoint_name = "your-sagemaker-endpoint"
agentcore_agent_arn     = ""  # Will be populated after agent deployment

# Monitoring and Scheduling
enable_monitoring          = true
sensor_simulation_schedule = "rate(1 minute)"
