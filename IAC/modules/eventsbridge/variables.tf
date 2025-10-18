variable "schedule_name" {
  description = "Name of the EventBridge rule"
  type        = string
}

variable "target_arn" {
  description = "ARN of the target Lambda function"
  type        = string
}