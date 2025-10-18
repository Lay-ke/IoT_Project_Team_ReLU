output "scheduled_event_arn" {
  description = "The ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.lambda_schedule.arn
}

output "rule_name" {
  description = "Name of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.lambda_schedule.name
}