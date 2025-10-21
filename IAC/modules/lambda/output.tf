output "conveyor_motor_simulator_lambda_function_arn" {
  description = "ARN of the Conveyor Motor Simulator Lambda function"
  value       = aws_lambda_function.conveyor_motor_simulator.arn
}

output "conveyor_motor_simulator_lambda_function_name" {
  description = "Name of the Conveyor Motor Simulator Lambda function"
  value       = aws_lambda_function.conveyor_motor_simulator.function_name
}

output "bedrock_agent_lambda_function_arn" {
  description = "ARN of the Bedrock Agent Lambda function"
  value       = aws_lambda_function.bedrock_agent.arn

}

output "bedrock_agent_lambda_function_name" {
  description = "Name of the Bedrock Agent Lambda function"
  value       = aws_lambda_function.bedrock_agent.function_name
}

output "feature_engineer_lambda_function_arn" {
  description = "ARN of the Feature Engineer Lambda function"
  value       = aws_lambda_function.feature_engineer.arn
}

output "feature_engineer_lambda_function_name" {
  description = "Name of the Feature Engineer Lambda function"
  value       = aws_lambda_function.feature_engineer.function_name
}

# New Lambda Functions Outputs
output "fetch_ml_inference_data_lambda_function_arn" {
  description = "ARN of the Fetch ML Inference Data Lambda function"
  value       = aws_lambda_function.fetch_ml_inference_data.arn
}

output "fetch_ml_inference_data_lambda_function_name" {
  description = "Name of the Fetch ML Inference Data Lambda function"
  value       = aws_lambda_function.fetch_ml_inference_data.function_name
}

output "fetch_raw_sensor_data_lambda_function_arn" {
  description = "ARN of the Fetch Raw Sensor Data Lambda function"
  value       = aws_lambda_function.fetch_raw_sensor_data.arn
}

output "fetch_raw_sensor_data_lambda_function_name" {
  description = "Name of the Fetch Raw Sensor Data Lambda function"
  value       = aws_lambda_function.fetch_raw_sensor_data.function_name
}

output "fetch_schedule_data_lambda_function_arn" {
  description = "ARN of the Fetch Schedule Data Lambda function"
  value       = aws_lambda_function.fetch_schedule_data.arn
}

output "fetch_schedule_data_lambda_function_name" {
  description = "Name of the Fetch Schedule Data Lambda function"
  value       = aws_lambda_function.fetch_schedule_data.function_name
}