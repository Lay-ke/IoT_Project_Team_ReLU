# Module for IAM Role and Policy for Lambda
resource "aws_iam_role" "lambda_role" {
    name = "lambda_s3_access_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "lambda.amazonaws.com"
                }
            }
        ]
    })
}

# IAM Policy for Lambda S3 Access
resource "aws_iam_policy" "lambda_s3_policy" {
    name        = "lambda_s3_access_policy"
    description = "Allow Lambda functions to access S3"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "s3:GetObject",
                    "s3:ListBucket"
                ]
                Resource = [
                    "arn:aws:s3:::*"
                ]
            }
        ]
    })
}

resource "aws_iam_policy" "lambda_iot_publish_policy" {
    name        = "lambda_iot_publish_policy"
    description = "Allow Lambda functions to publish to AWS IoT Core topics"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "iot:Publish"
                ]
                Resource = [
                    "*"
                ]
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "lambda_iot_publish_attach" {
    role       = aws_iam_role.lambda_role.name
    policy_arn = aws_iam_policy.lambda_iot_publish_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_s3_attach" {
    role       = aws_iam_role.lambda_role.name
    policy_arn = aws_iam_policy.lambda_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
    role       = aws_iam_role.lambda_role.name
    policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ------------------------------------------------------------------------------
# IAM role and policy for EventBridge Scheduler to invoke Lambda
# ------------------------------------------------------------------------------
resource "aws_iam_role" "eventbridge_scheduler_role" {
    name = "eventbridge_scheduler_invoke_lambda_role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Action = "sts:AssumeRole"
                Effect = "Allow"
                Principal = {
                    Service = "scheduler.amazonaws.com"
                }
            }
        ]
    })
  
}

resource "aws_iam_policy" "eventbridge_scheduler_invoke_lambda_policy" {
    name        = "eventbridge_scheduler_invoke_lambda_policy"
    description = "Allow EventBridge Scheduler to invoke Lambda functions"
    policy      = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Action = [
                    "lambda:InvokeFunction"
                ]
                Resource = [
                    "*"
                ]
            }
        ]
    })
}

resource "aws_iam_role_policy_attachment" "eventbridge_scheduler_invoke_lambda_attach" {
    role       = aws_iam_role.eventbridge_scheduler_role.name
    policy_arn = aws_iam_policy.eventbridge_scheduler_invoke_lambda_policy.arn
}