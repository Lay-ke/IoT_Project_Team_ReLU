output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.relu_api.id
}

output "api_gateway_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.relu_api.arn
}

output "api_gateway_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.relu_api.execution_arn
}

output "api_gateway_invoke_url" {
  description = "Invoke URL of the API Gateway"
  value       = aws_api_gateway_stage.relu_api_stage.invoke_url
}

output "api_gateway_stage_name" {
  description = "Stage name of the API Gateway"
  value       = aws_api_gateway_stage.relu_api_stage.stage_name
}

# Resource IDs for reference
output "ml_inference_resource_id" {
  description = "Resource ID for ml-inference path"
  value       = aws_api_gateway_resource.ml_inference.id
}

output "prompt_resource_id" {
  description = "Resource ID for prompt path"
  value       = aws_api_gateway_resource.prompt.id
}

output "schedules_resource_id" {
  description = "Resource ID for schedules path"
  value       = aws_api_gateway_resource.schedules.id
}

output "sensor_readings_resource_id" {
  description = "Resource ID for sensor-readings path"
  value       = aws_api_gateway_resource.sensor_readings.id
}

# Full endpoint URLs
output "endpoint_urls" {
  description = "Full endpoint URLs for all API paths"
  value = {
    ml_inference    = "${aws_api_gateway_stage.relu_api_stage.invoke_url}/ml-inference"
    prompt          = "${aws_api_gateway_stage.relu_api_stage.invoke_url}/prompt"
    schedules       = "${aws_api_gateway_stage.relu_api_stage.invoke_url}/schedules"
    sensor_readings = "${aws_api_gateway_stage.relu_api_stage.invoke_url}/sensor-readings"
  }
}