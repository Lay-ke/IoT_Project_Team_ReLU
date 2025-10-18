# EventBridge Rule for scheduled Lambda invocation
resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = var.schedule_name
  description         = "Trigger Lambda function on a schedule"
  schedule_expression = "rate(5 minutes)" # Every 5 minutes
}

# EventBridge Target for the Lambda function
resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "TriggerLambdaFunction"
  arn       = var.target_arn
}

# Lambda permission for EventBridge Rule
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.target_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}