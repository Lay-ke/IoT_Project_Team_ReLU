locals {
  parent_dir3 = path.cwd
}


resource "aws_lambda_function" "feature_engineer" {
  function_name = var.feature_engineer_lambda_name

  runtime = "python3.13"
  role    = var.feature_engineer_lambda_execution_role_arn
  handler = "${var.feature_engineer_lambda_name}.lambda_handler"

  # Path to your zipped Lambda function code (ensure the file is in the same directory or adjust the path)
  filename         = "${local.parent_dir3}/functions/${var.feature_engineer_lambda_name}.zip"
  source_code_hash = filebase64sha256("${local.parent_dir3}/functions/${var.feature_engineer_lambda_name}.zip")

  # Timeout and memory settings (adjust as needed)
  timeout     = 180
  memory_size = 256
  environment {
    variables = var.app_env_vars
  }
}


# # Grant feature_engineer permission to invoke the 
# resource "aws_lambda_permission" "feature_engineer_policy" {
#   statement_id  = "AllowFeatureEngineerInvoke"
#   action        = "lambda:InvokeFunction"
#   principal     = "bedrock.amazonaws.com"
#   function_name = aws_lambda_function.feature_engineer.function_name
#   source_arn    = var.bedrock_agent_arn
# }
