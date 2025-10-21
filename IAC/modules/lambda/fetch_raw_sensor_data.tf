locals {
  parent_dir_sensor_data = path.cwd
}

resource "aws_lambda_function" "fetch_raw_sensor_data" {
  function_name = var.fetch_raw_sensor_data_lambda_name

  runtime = "python3.13"
  role    = var.fetch_raw_sensor_data_lambda_execution_role_arn
  handler = "${var.fetch_raw_sensor_data_lambda_name}.lambda_handler"

  # Path to your zipped Lambda function code
  filename         = "${local.parent_dir_sensor_data}/functions/${var.fetch_raw_sensor_data_lambda_name}.zip"
  source_code_hash = filebase64sha256("${local.parent_dir_sensor_data}/functions/${var.fetch_raw_sensor_data_lambda_name}.zip")

  # Timeout and memory settings
  timeout     = 180
  memory_size = 256
  environment {
    variables = var.app_env_vars
  }

  tags = {
    Name        = var.fetch_raw_sensor_data_lambda_name
    Environment = var.app_env_vars["environment"]
    Purpose     = "Raw Sensor Data Fetcher"
  }
}