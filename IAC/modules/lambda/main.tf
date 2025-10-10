locals {
  parent_dir2 = path.cwd
}


resource "aws_lambda_function" "conveyor_motor_simulator" {
  function_name = var.conveyor_motor_simulator_lambda_name

  runtime = "python3.13"
  role    = var.conveyor_motor_simulator_lambda_execution_role_arn
  handler = "${var.conveyor_motor_simulator_lambda_name}.lambda_handler"

  # Path to your zipped Lambda function code (ensure the file is in the same directory or adjust the path)
  filename         = "${local.parent_dir2}/functions/${var.conveyor_motor_simulator_lambda_name}.zip"
  source_code_hash = filebase64sha256("${local.parent_dir2}/functions/${var.conveyor_motor_simulator_lambda_name}.zip")

  # Timeout and memory settings (adjust as needed)
  timeout     = 60
  memory_size = 128
  environment {
    variables = var.app_env_vars
  }
}

# Note: EventBridge Scheduler Lambda permission is created in main.tf to avoid circular dependency

# resource "aws_lambda_permission" "iot_topic_rule" {
#   statement_id  = "AllowIoTInvoke"
#   action        = "lambda:InvokeFunction"
#   principal     = "iot.amazonaws.com"
#   function_name = aws_lambda_function.update_asg_capacity.function_name
#   source_arn    = var.active_dr_sns_topic_arn
# }