# API Gateway Module

This module creates a RESTful API Gateway for the Predictive Maintenance Forecaster (PMF) project with Lambda proxy integrations and CORS support.

## Resources Created

### API Gateway Resources
- **REST API** - Regional API Gateway for PMF endpoints
- **API Paths** - Four main endpoint paths:
  - `/ml-inference` (POST) - Machine learning inference endpoint
  - `/prompt` (POST) - AI prompt processing endpoint  
  - `/schedules` (GET) - Maintenance schedules retrieval
  - `/sensor-readings` (GET) - Sensor data retrieval
- **CORS Support** - OPTIONS methods with CORS headers for all paths
- **Lambda Integrations** - AWS_PROXY integrations for seamless Lambda connectivity
- **API Stage** - Deployment stage for the API

### Additional Features
- Lambda permissions for API Gateway invocation
- Comprehensive CORS configuration
- Regional endpoint type for optimal performance

## API Endpoints

| Path | Method | Purpose | Lambda Function |
|------|--------|---------|----------------|
| `/ml-inference` | POST | ML model inference requests | Feature Engineer Lambda |
| `/prompt` | POST | AI prompt processing | Bedrock Agent Lambda |
| `/schedules` | GET | Retrieve maintenance schedules | Conveyor Motor Simulator Lambda |
| `/sensor-readings` | GET | Get sensor data | Feature Engineer Lambda |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| api_name | Name of the API Gateway | `string` | `"relu-pmf-api"` | no |
| environment | The deployment environment | `string` | n/a | yes |
| stage_name | Stage name for API Gateway deployment | `string` | `"prod"` | no |
| aws_region | AWS region | `string` | n/a | yes |
| ml_inference_lambda_function_arn | ARN of the ML inference Lambda function | `string` | n/a | yes |
| prompt_lambda_function_arn | ARN of the prompt Lambda function | `string` | n/a | yes |
| schedules_lambda_function_arn | ARN of the schedules Lambda function | `string` | n/a | yes |
| sensor_readings_lambda_function_arn | ARN of the sensor readings Lambda function | `string` | n/a | yes |
| ml_inference_lambda_function_name | Name of the ML inference Lambda function | `string` | n/a | yes |
| prompt_lambda_function_name | Name of the prompt Lambda function | `string` | n/a | yes |
| schedules_lambda_function_name | Name of the schedules Lambda function | `string` | n/a | yes |
| sensor_readings_lambda_function_name | Name of the sensor readings Lambda function | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| api_gateway_id | ID of the API Gateway |
| api_gateway_arn | ARN of the API Gateway |
| api_gateway_execution_arn | Execution ARN of the API Gateway |
| api_gateway_invoke_url | Base invoke URL of the API Gateway |
| api_gateway_stage_name | Stage name of the API Gateway |
| endpoint_urls | Full endpoint URLs for all API paths |

## Usage

```hcl
module "api_gateway" {
  source = "./modules/api_gateway"

  api_name                                 = "relu-pmf-api"
  environment                              = var.environment
  stage_name                               = "prod"
  aws_region                               = var.aws_region
  
  # Lambda function ARNs
  ml_inference_lambda_function_arn         = module.lambda.feature_engineer_lambda_function_arn
  prompt_lambda_function_arn               = module.lambda.bedrock_agent_lambda_function_arn
  schedules_lambda_function_arn            = module.lambda.conveyor_motor_simulator_lambda_function_arn
  sensor_readings_lambda_function_arn      = module.lambda.feature_engineer_lambda_function_arn
  
  # Lambda function names
  ml_inference_lambda_function_name        = module.lambda.feature_engineer_lambda_function_name
  prompt_lambda_function_name              = module.lambda.bedrock_agent_lambda_function_name
  schedules_lambda_function_name           = module.lambda.conveyor_motor_simulator_lambda_function_name
  sensor_readings_lambda_function_name     = module.lambda.feature_engineer_lambda_function_name
}
```

## CORS Configuration

All endpoints are configured with CORS support to enable cross-origin requests from web applications:

- **Access-Control-Allow-Origin**: `*` (allows all origins)
- **Access-Control-Allow-Methods**: `GET,OPTIONS,POST,PUT`
- **Access-Control-Allow-Headers**: Standard headers for API requests

## Integration Type

Uses **AWS_PROXY** integration which:
- Passes the entire request to Lambda
- Expects Lambda to return properly formatted response
- Simplifies Lambda function development
- Supports all HTTP methods and headers

## Example API Calls

```bash
# ML Inference
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/ml-inference \
  -H "Content-Type: application/json" \
  -d '{"sensor_data": {...}}'

# AI Prompt
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Analyze conveyor health"}'

# Get Schedules
curl -X GET https://your-api-id.execute-api.region.amazonaws.com/prod/schedules

# Get Sensor Readings
curl -X GET https://your-api-id.execute-api.region.amazonaws.com/prod/sensor-readings
```