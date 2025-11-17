output "parameter_paths" {
  description = "SSM parameter paths"
  value = {
    aws_region            = aws_ssm_parameter.aws_region.name
    bedrock_region        = aws_ssm_parameter.bedrock_region.name
    bedrock_model_id      = aws_ssm_parameter.bedrock_model_id.name
    knowledge_base_id     = aws_ssm_parameter.knowledge_base_id.name
    knowledge_base_region = aws_ssm_parameter.knowledge_base_region.name
    work_schedule_bucket  = aws_ssm_parameter.work_schedule_bucket.name
    work_schedule_prefix  = aws_ssm_parameter.work_schedule_prefix.name
    environment           = aws_ssm_parameter.environment.name
    log_level             = aws_ssm_parameter.log_level.name
  }
}
