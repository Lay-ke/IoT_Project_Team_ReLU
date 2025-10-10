output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_role.arn
  
}

output "eventbridge_scheduler_role_arn" {
  description = "ARN of the EventBridge Scheduler role"
  value       = aws_iam_role.eventbridge_scheduler_role.arn
}
