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
