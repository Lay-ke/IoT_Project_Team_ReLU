# API Gateway REST API
resource "aws_api_gateway_rest_api" "relu_api" {
  name        = var.api_name
  description = "API Gateway for Predictive Maintenance Forecaster (PMF)"
  
  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = var.api_name
    Environment = var.environment
    Purpose     = "PMF API Gateway"
  }
}

# API Gateway Resources (Paths)
resource "aws_api_gateway_resource" "ml_inference" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  parent_id   = aws_api_gateway_rest_api.relu_api.root_resource_id
  path_part   = "ml-inference"
}

resource "aws_api_gateway_resource" "prompt" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  parent_id   = aws_api_gateway_rest_api.relu_api.root_resource_id
  path_part   = "prompt"
}

resource "aws_api_gateway_resource" "schedules" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  parent_id   = aws_api_gateway_rest_api.relu_api.root_resource_id
  path_part   = "schedules"
}

resource "aws_api_gateway_resource" "sensor_readings" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  parent_id   = aws_api_gateway_rest_api.relu_api.root_resource_id
  path_part   = "sensor-readings"
}

# API Gateway Methods
# ml-inference POST method
resource "aws_api_gateway_method" "ml_inference_post" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.ml_inference.id
  http_method   = "GET"
  authorization = "NONE"
}

# prompt POST method
resource "aws_api_gateway_method" "prompt_post" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.prompt.id
  http_method   = "POST"
  authorization = "NONE"
}

# schedules GET method
resource "aws_api_gateway_method" "schedules_get" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.schedules.id
  http_method   = "GET"
  authorization = "NONE"
}

# sensor-readings GET method
resource "aws_api_gateway_method" "sensor_readings_get" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.sensor_readings.id
  http_method   = "GET"
  authorization = "NONE"
}

# Lambda Integrations
# ml-inference Lambda integration
resource "aws_api_gateway_integration" "ml_inference_lambda" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.ml_inference.id
  http_method = aws_api_gateway_method.ml_inference_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.ml_inference_lambda_function_arn}/invocations"
}

# prompt Lambda integration
resource "aws_api_gateway_integration" "prompt_lambda" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.prompt.id
  http_method = aws_api_gateway_method.prompt_post.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.prompt_lambda_function_arn}/invocations"
}

# schedules Lambda integration
resource "aws_api_gateway_integration" "schedules_lambda" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.schedules.id
  http_method = aws_api_gateway_method.schedules_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.schedules_lambda_function_arn}/invocations"
}

# sensor-readings Lambda integration
resource "aws_api_gateway_integration" "sensor_readings_lambda" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.sensor_readings.id
  http_method = aws_api_gateway_method.sensor_readings_get.http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${var.sensor_readings_lambda_function_arn}/invocations"
}

# CORS Configuration for all resources
# ml-inference OPTIONS method for CORS
resource "aws_api_gateway_method" "ml_inference_options" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.ml_inference.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "ml_inference_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.ml_inference.id
  http_method = aws_api_gateway_method.ml_inference_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "ml_inference_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.ml_inference.id
  http_method = aws_api_gateway_method.ml_inference_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "ml_inference_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.ml_inference.id
  http_method = aws_api_gateway_method.ml_inference_options.http_method
  status_code = aws_api_gateway_method_response.ml_inference_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Similar CORS setup for other resources...
# prompt OPTIONS method for CORS
resource "aws_api_gateway_method" "prompt_options" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.prompt.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "prompt_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.prompt.id
  http_method = aws_api_gateway_method.prompt_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "prompt_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.prompt.id
  http_method = aws_api_gateway_method.prompt_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "prompt_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.prompt.id
  http_method = aws_api_gateway_method.prompt_options.http_method
  status_code = aws_api_gateway_method_response.prompt_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# schedules OPTIONS method for CORS
resource "aws_api_gateway_method" "schedules_options" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.schedules.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "schedules_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.schedules.id
  http_method = aws_api_gateway_method.schedules_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "schedules_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.schedules.id
  http_method = aws_api_gateway_method.schedules_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "schedules_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.schedules.id
  http_method = aws_api_gateway_method.schedules_options.http_method
  status_code = aws_api_gateway_method_response.schedules_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# sensor-readings OPTIONS method for CORS
resource "aws_api_gateway_method" "sensor_readings_options" {
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  resource_id   = aws_api_gateway_resource.sensor_readings.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "sensor_readings_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.sensor_readings.id
  http_method = aws_api_gateway_method.sensor_readings_options.http_method

  type = "MOCK"
  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "sensor_readings_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.sensor_readings.id
  http_method = aws_api_gateway_method.sensor_readings_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "sensor_readings_options" {
  rest_api_id = aws_api_gateway_rest_api.relu_api.id
  resource_id = aws_api_gateway_resource.sensor_readings.id
  http_method = aws_api_gateway_method.sensor_readings_options.http_method
  status_code = aws_api_gateway_method_response.sensor_readings_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "relu_api_deployment" {
  depends_on = [
    aws_api_gateway_integration.ml_inference_lambda,
    aws_api_gateway_integration.prompt_lambda,
    aws_api_gateway_integration.schedules_lambda,
    aws_api_gateway_integration.sensor_readings_lambda,
    aws_api_gateway_integration.ml_inference_options,
    aws_api_gateway_integration.prompt_options,
    aws_api_gateway_integration.schedules_options,
    aws_api_gateway_integration.sensor_readings_options,
  ]

  rest_api_id = aws_api_gateway_rest_api.relu_api.id

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "relu_api_stage" {
  deployment_id = aws_api_gateway_deployment.relu_api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.relu_api.id
  stage_name    = var.stage_name

  tags = {
    Name        = "${var.api_name}-${var.stage_name}"
    Environment = var.environment
  }
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "api_gateway_ml_inference" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.ml_inference_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.relu_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_prompt" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.prompt_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.relu_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_schedules" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.schedules_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.relu_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "api_gateway_sensor_readings" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.sensor_readings_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.relu_api.execution_arn}/*/*"
}