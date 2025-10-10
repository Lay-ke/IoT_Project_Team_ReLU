locals {
  parent_dir = path.cwd
}


resource "aws_lambda_function" "bedrock_agent" {
  function_name = var.bedrock_agent_lambda_name

  runtime = "python3.13"
  role    = var.bedrock_agent_lambda_execution_role_arn
  handler = "${var.bedrock_agent_lambda_name}.lambda_handler"

  # Path to your zipped Lambda function code (ensure the file is in the same directory or adjust the path)
  filename         = "${local.parent_dir}/functions/${var.bedrock_agent_lambda_name}.zip"
  source_code_hash = filebase64sha256("${local.parent_dir}/functions/${var.bedrock_agent_lambda_name}.zip")

  # Timeout and memory settings (adjust as needed)
  timeout     = 60
  memory_size = 128
  environment {
    variables = var.app_env_vars
  }
}


# Grant bedrock permission to invoke the Lambda function in the DR region
resource "aws_lambda_permission" "bedrock_agent_policy" {
  statement_id  = "AllowBedrockAgentInvoke"
  action        = "lambda:InvokeFunction"
  principal     = "bedrock.amazonaws.com"
  function_name = aws_lambda_function.bedrock_agent.function_name
  source_arn    = var.bedrock_agent_arn
}

# resource "aws_lambda_permission" "iot_topic_rule" {
#   statement_id  = "AllowIoTInvoke"
#   action        = "lambda:InvokeFunction"
#   principal     = "iot.amazonaws.com"
#   function_name = aws_lambda_function.update_asg_capacity.function_name
#   source_arn    = var.
# }